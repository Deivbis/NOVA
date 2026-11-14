import threading

from nova.core import CoreOrchestrator, EventNames, NovaState, Result
from nova.voice import AudioData, RecordingResult, VoiceInputService


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


def speech_recording():
    return Result.ok(
        RecordingResult(
            audio=AudioData(
                pcm=b"\x00\x00" * 100,
                sample_rate=16000,
                provider="microphone",
            ),
            reason="speech_ended",
            seconds=1.7,
            peak_rms=0.09,
        )
    )


def silent_recording():
    return Result.ok(
        RecordingResult(
            audio=None,
            reason="no_speech",
            seconds=6.0,
            peak_rms=0.001,
        )
    )


class FakeRecorder:
    def __init__(self, result=None, on_record=None):
        self.result = speech_recording() if result is None else result
        self.on_record = on_record
        self.calls = 0

    def record(self, cancel_event):
        self.calls += 1

        if self.on_record is not None:
            self.on_record()

        return self.result


class BlockingRecorder:
    def __init__(self):
        self.started = threading.Event()
        self.finished = threading.Event()

    def record(self, cancel_event):
        self.started.set()
        cancel_event.wait(3)
        self.finished.set()

        return Result.ok(
            RecordingResult(
                audio=None,
                reason="cancelled",
                seconds=0.0,
                peak_rms=0.0,
            )
        )


class FakeSTT:
    def __init__(self, result=None):
        self.result = Result.ok("abre el navegador") if result is None else result
        self.calls = []
        self.shut_down = False

    def transcribe(self, audio, language="es"):
        self.calls.append(audio)

        return self.result

    def shutdown(self):
        self.shut_down = True


class FakeVoiceOutput:
    def __init__(self, speaking=False):
        self.is_speaking = speaking
        self.stopped = 0

    def stop(self):
        self.stopped += 1


def create_core():
    core = CoreOrchestrator()
    core.start()

    return core


def collect_events(core):
    events = []
    core.subscribe(events.append)

    return events


def voice_names(events):
    return [e.name for e in events if e.name.startswith("voice.")]


def create_service(
    core,
    recorder=None,
    stt=None,
    voice_output=None,
    handler=None,
    thread_factory=ImmediateThread,
):
    return VoiceInputService(
        core=core,
        recorder=recorder or FakeRecorder(),
        stt=stt or FakeSTT(),
        voice_output=voice_output,
        on_transcript=handler,
        thread_factory=thread_factory,
    )


def test_transcript_is_delivered_and_the_chat_takes_over_the_state():
    core = create_core()
    events = collect_events(core)
    texts = []
    service = create_service(core, handler=texts.append)

    assert service.start_listening() is True

    assert texts == ["abre el navegador"]
    assert core.state == NovaState.PROCESSING
    assert voice_names(events) == [
        EventNames.VOICE_LISTENING_STARTED,
        EventNames.VOICE_LISTENING_STOPPED,
    ]


def test_state_is_listening_while_recording():
    core = create_core()
    seen = {}
    recorder = FakeRecorder(
        on_record=lambda: seen.update(state=core.state)
    )
    service = create_service(core, recorder=recorder)

    service.start_listening()

    assert seen["state"] == NovaState.LISTENING


def test_without_a_receiver_the_state_returns_to_idle():
    core = create_core()
    service = create_service(core, handler=None)

    service.start_listening()

    assert core.state == NovaState.IDLE
    assert service.is_active is False


def test_no_speech_publishes_an_input_error_and_skips_the_stt():
    core = create_core()
    events = collect_events(core)
    stt = FakeSTT()
    texts = []
    service = create_service(
        core,
        recorder=FakeRecorder(result=silent_recording()),
        stt=stt,
        handler=texts.append,
    )

    service.start_listening()

    error = next(e for e in events if e.name == EventNames.VOICE_ERROR)

    assert error.payload["code"] == "NO_SPEECH_DETECTED"
    assert error.payload["direction"] == "input"
    assert stt.calls == []
    assert texts == []
    assert core.state == NovaState.IDLE


def test_microphone_error_publishes_an_input_error():
    core = create_core()
    events = collect_events(core)
    recorder = FakeRecorder(
        result=Result.fail(
            code="MICROPHONE_ERROR",
            message="No se pudo abrir el micrófono.",
        )
    )
    service = create_service(core, recorder=recorder)

    service.start_listening()

    assert voice_names(events) == [
        EventNames.VOICE_LISTENING_STARTED,
        EventNames.VOICE_ERROR,
    ]
    assert core.state == NovaState.IDLE


def test_stt_failure_publishes_an_input_error():
    core = create_core()
    events = collect_events(core)
    texts = []
    stt = FakeSTT(
        result=Result.fail(code="STT_ERROR", message="No se pudo transcribir.")
    )
    service = create_service(core, stt=stt, handler=texts.append)

    service.start_listening()

    error = next(e for e in events if e.name == EventNames.VOICE_ERROR)

    assert error.payload["code"] == "STT_ERROR"
    assert texts == []
    assert core.state == NovaState.IDLE


def test_events_never_include_the_transcript():
    core = create_core()
    events = collect_events(core)
    service = create_service(core, handler=lambda text: None)

    service.start_listening()

    assert "abre el navegador" not in str([e.payload for e in events])


def test_a_failing_receiver_is_contained():
    core = create_core()

    def broken(text):
        raise RuntimeError("fallo del receptor")

    service = create_service(core, handler=broken)

    assert service.start_listening() is True
    assert core.state == NovaState.IDLE


def test_listening_is_ignored_while_nova_is_busy():
    core = create_core()
    core.set_state(NovaState.PROCESSING)
    recorder = FakeRecorder()
    service = create_service(core, recorder=recorder)

    assert service.start_listening() is False
    assert recorder.calls == 0


def test_listening_can_start_from_the_error_state():
    core = create_core()
    core.set_state(NovaState.ERROR)
    recorder = FakeRecorder()
    service = create_service(core, recorder=recorder)

    assert service.start_listening() is True
    assert recorder.calls == 1


def test_toggle_starts_listening_when_idle():
    core = create_core()
    service = create_service(core)

    assert service.toggle() == "started"


def test_toggle_interrupts_the_voice_first():
    core = create_core()
    voice_output = FakeVoiceOutput(speaking=True)
    recorder = FakeRecorder()
    service = create_service(
        core,
        recorder=recorder,
        voice_output=voice_output,
    )

    assert service.toggle() == "stopped_speaking"
    assert voice_output.stopped == 1
    assert recorder.calls == 0


def test_toggle_cancels_an_active_listening():
    core = create_core()
    events = collect_events(core)
    recorder = BlockingRecorder()
    texts = []
    service = create_service(
        core,
        recorder=recorder,
        handler=texts.append,
        thread_factory=threading.Thread,
    )

    assert service.start_listening() is True
    assert recorder.started.wait(3)

    assert service.toggle() == "cancelled"
    assert recorder.finished.wait(3)

    stopped = next(
        e for e in events if e.name == EventNames.VOICE_LISTENING_STOPPED
    )

    assert stopped.payload["reason"] == "cancelled"
    assert core.state == NovaState.IDLE
    assert service.is_active is False
    assert texts == []


def test_shutdown_rejects_new_listening_and_closes_the_stt():
    core = create_core()
    stt = FakeSTT()
    service = create_service(core, stt=stt)

    service.shutdown()

    assert service.start_listening() is False
    assert stt.shut_down is True