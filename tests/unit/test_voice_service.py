import logging
import threading
import time

from nova.core import (
    CoreOrchestrator,
    EventNames,
    Identity,
    NovaState,
    Result,
)
from nova.voice import AudioData, VoiceService, VoiceSettings


class ImmediateThread:
    """Hilo falso: ejecuta el objetivo de inmediato, de forma síncrona."""

    def __init__(self, target, args=(), name=None, daemon=None):
        self._target = target
        self._args = args

    def start(self):
        self._target(*self._args)

    def is_alive(self):
        return False

    def join(self, timeout=None):
        pass


class FakeRouter:
    def __init__(self, fail=False, error=None):
        self.fail = fail
        self.error = error
        self.calls = []
        self.prefer_online = False

    def synthesize(self, text, identity):
        self.calls.append((text, identity))

        if self.error is not None:
            raise self.error

        if self.fail:
            return Result.fail(code="TTS_FAILED", message="fallo simulado")

        return Result.ok(
            AudioData(
                pcm=b"\x00\x00" * 100,
                sample_rate=22050,
                provider="fake",
            )
        )


class FakePlayer:
    def __init__(self, block=False, fail=False):
        self.block = block
        self.fail = fail
        self.played = []
        self.stopped = 0
        self.started = threading.Event()
        self.on_play = None
        self._release = threading.Event()

    def play(self, audio):
        self.played.append(audio)
        self.started.set()

        if self.on_play is not None:
            self.on_play()

        if self.block:
            self._release.wait(3)

        if self.fail:
            return Result.fail(
                code="AUDIO_PLAYBACK_ERROR",
                message="sin salida de audio",
            )

        return Result.ok()

    def stop(self):
        self.stopped += 1
        self._release.set()


def create_core():
    core = CoreOrchestrator()
    core.start()

    return core


def collect_events(core):
    events = []
    core.subscribe(events.append)

    return events


def voice_names(events):
    return [event.name for event in events if event.name.startswith("voice.")]


def create_service(
    core,
    router=None,
    player=None,
    settings=None,
    save=None,
    thread_factory=ImmediateThread,
):
    return VoiceService(
        core=core,
        router=router or FakeRouter(),
        player=player or FakePlayer(),
        settings=settings or VoiceSettings(enabled=True),
        save_settings=save,
        thread_factory=thread_factory,
    )


def wait_for(condition, timeout=3.0):
    deadline = time.monotonic() + timeout

    while time.monotonic() < deadline:
        if condition():
            return True

        time.sleep(0.01)

    return False


def test_disabled_voice_does_not_speak():
    core = create_core()
    router = FakeRouter()
    service = create_service(
        core,
        router=router,
        settings=VoiceSettings(enabled=False),
    )

    assert service.speak("Hola") is False
    assert router.calls == []
    assert core.state == NovaState.IDLE


def test_empty_text_is_not_spoken():
    core = create_core()
    router = FakeRouter()
    service = create_service(core, router=router)

    assert service.speak("   ") is False
    assert router.calls == []


def test_speaking_sets_state_plays_audio_and_returns_to_idle():
    core = create_core()
    events = collect_events(core)
    router = FakeRouter()
    player = FakePlayer()
    service = create_service(
        core,
        router=router,
        player=player,
        settings=VoiceSettings(enabled=True, identity=Identity.ASTI),
    )
    seen = {}
    player.on_play = lambda: seen.update(
        state=core.state,
        speaking=service.is_speaking,
    )

    assert service.speak("Buenos días, Jefe") is True

    assert router.calls == [("Buenos días, Jefe", Identity.ASTI)]
    assert seen == {"state": NovaState.SPEAKING, "speaking": True}
    assert len(player.played) == 1
    assert core.state == NovaState.IDLE
    assert service.is_speaking is False
    assert voice_names(events) == [
        EventNames.VOICE_SPEAKING_STARTED,
        EventNames.VOICE_SPEAKING_FINISHED,
    ]


def test_events_never_include_the_spoken_text():
    core = create_core()
    events = collect_events(core)
    service = create_service(core)

    service.speak("secreto-123")

    assert "secreto-123" not in str([event.payload for event in events])


def test_synthesis_failure_publishes_error_and_returns_to_idle():
    core = create_core()
    events = collect_events(core)
    player = FakePlayer()
    service = create_service(core, router=FakeRouter(fail=True), player=player)

    service.speak("Hola")

    error = next(e for e in events if e.name == EventNames.VOICE_ERROR)

    assert player.played == []
    assert error.payload["code"] == "TTS_FAILED"
    assert core.state == NovaState.IDLE
    assert voice_names(events) == [
        EventNames.VOICE_ERROR,
        EventNames.VOICE_SPEAKING_FINISHED,
    ]


def test_playback_failure_publishes_error():
    core = create_core()
    events = collect_events(core)
    service = create_service(core, player=FakePlayer(fail=True))

    service.speak("Hola")

    error = next(e for e in events if e.name == EventNames.VOICE_ERROR)

    assert error.payload["code"] == "AUDIO_PLAYBACK_ERROR"
    assert voice_names(events) == [
        EventNames.VOICE_SPEAKING_STARTED,
        EventNames.VOICE_ERROR,
        EventNames.VOICE_SPEAKING_FINISHED,
    ]


def test_unexpected_exception_is_handled(caplog):
    core = create_core()
    events = collect_events(core)
    router = FakeRouter(error=RuntimeError("boom"))
    service = create_service(core, router=router)

    with caplog.at_level(logging.ERROR, logger="nova"):
        service.speak("Hola")

    error = next(e for e in events if e.name == EventNames.VOICE_ERROR)

    assert error.payload["code"] == "VOICE_UNEXPECTED_ERROR"
    assert core.state == NovaState.IDLE
    assert service.is_speaking is False


def test_stop_cancels_current_speech():
    core = create_core()
    events = collect_events(core)
    player = FakePlayer(block=True)
    service = create_service(
        core,
        player=player,
        thread_factory=threading.Thread,
    )

    assert service.speak("Una respuesta larga") is True
    assert player.started.wait(3)

    service.stop()

    assert player.stopped == 1
    assert core.state == NovaState.IDLE
    assert service.is_speaking is False
    assert wait_for(lambda: not service._thread.is_alive())

    finished = [
        e for e in events if e.name == EventNames.VOICE_SPEAKING_FINISHED
    ]

    assert len(finished) == 1
    assert finished[0].payload["cancelled"] is True


def test_new_speech_replaces_the_previous_one():
    core = create_core()
    player = FakePlayer(block=True)
    service = create_service(
        core,
        player=player,
        thread_factory=threading.Thread,
    )

    service.speak("uno")
    assert player.started.wait(3)

    service.speak("dos")

    assert wait_for(lambda: len(player.played) == 2)
    assert player.stopped >= 1
    assert wait_for(lambda: not service.is_speaking)
    assert core.state == NovaState.IDLE


def test_update_settings_applies_and_persists():
    core = create_core()
    router = FakeRouter()
    saved = []
    service = create_service(core, router=router, save=saved.append)

    service.update_settings(identity=Identity.ASTI, prefer_online=True)

    assert service.settings.identity == Identity.ASTI
    assert router.prefer_online is True
    assert saved == [service.settings]

    service.speak("Hola")

    assert router.calls[0][1] == Identity.ASTI


def test_disabling_voice_stops_speech():
    core = create_core()
    player = FakePlayer(block=True)
    service = create_service(
        core,
        player=player,
        thread_factory=threading.Thread,
    )

    service.speak("Hola")
    assert player.started.wait(3)

    service.update_settings(enabled=False)

    assert player.stopped == 1
    assert service.is_speaking is False
    assert service.speak("Otra vez") is False


def test_save_failure_does_not_raise():
    core = create_core()

    def broken(settings):
        raise OSError("disco lleno")

    service = create_service(core, save=broken)

    service.update_settings(identity=Identity.ASTI)

    assert service.settings.identity == Identity.ASTI


def test_shutdown_stops_speech_and_rejects_new_speech():
    core = create_core()
    player = FakePlayer()
    service = create_service(core, player=player)

    service.shutdown()

    assert player.stopped == 1
    assert service.speak("Hola") is False



def test_output_errors_are_marked_with_their_direction():
    core = create_core()
    events = collect_events(core)
    service = create_service(core, router=FakeRouter(fail=True))

    service.speak("Hola")

    error = next(e for e in events if e.name == EventNames.VOICE_ERROR)

    assert error.payload["direction"] == "output"



FIRST = "Esta es la primera frase de la respuesta."
SECOND = "Esta es la segunda frase de la respuesta."
THIRD = "Y esta es la tercera frase de la respuesta."


class SignalingRouter(FakeRouter):
    def __init__(self, signal_text):
        super().__init__()
        self.signal_text = signal_text
        self.requested = threading.Event()

    def synthesize(self, text, identity):
        if text == self.signal_text:
            self.requested.set()

        return super().synthesize(text, identity)


class FailOnSecondRouter(FakeRouter):
    def synthesize(self, text, identity):
        if text == SECOND:
            self.calls.append((text, identity))

            return Result.fail(code="TTS_FAILED", message="fallo simulado")

        return super().synthesize(text, identity)


def test_sentences_are_synthesized_and_played_in_order():
    core = create_core()
    events = collect_events(core)
    router = FakeRouter()
    player = FakePlayer()
    service = create_service(core, router=router, player=player)

    service.speak(f"{FIRST} {SECOND}")

    started = next(
        e for e in events if e.name == EventNames.VOICE_SPEAKING_STARTED
    )

    assert [call[0] for call in router.calls] == [FIRST, SECOND]
    assert len(player.played) == 2
    assert started.payload["sentences"] == 2
    assert voice_names(events) == [
        EventNames.VOICE_SPEAKING_STARTED,
        EventNames.VOICE_SPEAKING_FINISHED,
    ]
    assert core.state == NovaState.IDLE


def test_next_sentence_is_synthesized_while_the_current_one_plays():
    core = create_core()
    router = SignalingRouter(SECOND)
    player = FakePlayer()
    overlaps = []

    def on_first_play():
        if not overlaps:
            overlaps.append(router.requested.wait(2))

    player.on_play = on_first_play
    service = create_service(core, router=router, player=player)

    service.speak(f"{FIRST} {SECOND}")

    assert overlaps == [True]


def test_failure_in_a_later_sentence_stops_and_reports_once():
    core = create_core()
    events = collect_events(core)
    player = FakePlayer()
    service = create_service(
        core,
        router=FailOnSecondRouter(),
        player=player,
    )

    service.speak(f"{FIRST} {SECOND} {THIRD}")

    errors = [e for e in events if e.name == EventNames.VOICE_ERROR]

    assert len(errors) == 1
    assert errors[0].payload["code"] == "TTS_FAILED"
    assert len(player.played) == 1
    assert voice_names(events) == [
        EventNames.VOICE_SPEAKING_STARTED,
        EventNames.VOICE_ERROR,
        EventNames.VOICE_SPEAKING_FINISHED,
    ]


def test_text_without_speakable_content_is_not_spoken():
    core = create_core()
    router = FakeRouter()
    service = create_service(core, router=router)

    assert service.speak("😊 🌞") is False
    assert router.calls == []
    assert core.state == NovaState.IDLE


def test_markdown_and_emojis_are_removed_before_synthesis():
    core = create_core()
    router = FakeRouter()
    service = create_service(core, router=router)

    service.speak("¡Hola, **Deivbis**! 😊 Todo está listo para trabajar.")

    spoken = router.calls[0][0]

    assert "*" not in spoken
    assert "😊" not in spoken
    assert "Deivbis" in spoken


def test_stop_cancels_the_remaining_sentences():
    core = create_core()
    player = FakePlayer(block=True)
    service = create_service(
        core,
        player=player,
        thread_factory=threading.Thread,
    )

    service.speak(f"{FIRST} {SECOND}")
    assert player.started.wait(3)

    service.stop()

    assert wait_for(lambda: not service._thread.is_alive())
    assert len(player.played) == 1
    assert core.state == NovaState.IDLE