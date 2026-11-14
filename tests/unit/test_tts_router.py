import logging

from nova.core import ConnectivityState, Identity, Result
from nova.voice import AudioData, TTSRouter


class FakeTTS:
    def __init__(self, name, fail=False):
        self.name = name
        self.requires_internet = False
        self.fail = fail
        self.calls = []

    def synthesize(self, text, identity):
        self.calls.append((text, identity))

        if self.fail:
            return Result.fail(
                code="TTS_FAILED",
                message="fallo simulado",
            )

        return Result.ok(
            AudioData(
                pcm=b"\x00\x00" * 100,
                sample_rate=22050,
                provider=self.name,
            )
        )


class FakeClock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now


def create_router(
    online=None,
    prefer_online=False,
    connectivity=ConnectivityState.UNKNOWN,
    clock=None,
):
    local = FakeTTS("local")
    router = TTSRouter(
        local=local,
        online=online,
        prefer_online=prefer_online,
        connectivity=lambda: connectivity,
        clock=clock or FakeClock(),
    )

    return router, local


def test_local_voice_is_used_by_default():
    online = FakeTTS("online")
    router, local = create_router(online=online)

    result = router.synthesize("Hola", Identity.ATLAS)

    assert result.value.provider == "local"
    assert online.calls == []


def test_online_voice_is_used_when_preferred_and_online():
    online = FakeTTS("online")
    router, local = create_router(
        online=online,
        prefer_online=True,
        connectivity=ConnectivityState.ONLINE,
    )

    result = router.synthesize("Hola", Identity.ASTI)

    assert result.value.provider == "online"
    assert local.calls == []


def test_online_voice_is_tried_when_connectivity_is_unknown():
    online = FakeTTS("online")
    router, _ = create_router(online=online, prefer_online=True)

    result = router.synthesize("Hola", Identity.ASTI)

    assert result.value.provider == "online"


def test_online_voice_is_skipped_when_offline():
    online = FakeTTS("online")
    router, _ = create_router(
        online=online,
        prefer_online=True,
        connectivity=ConnectivityState.OFFLINE,
    )

    result = router.synthesize("Hola", Identity.ASTI)

    assert result.value.provider == "local"
    assert online.calls == []


def test_online_failure_falls_back_to_local_voice(caplog):
    online = FakeTTS("online", fail=True)
    router, _ = create_router(online=online, prefer_online=True)

    with caplog.at_level(logging.WARNING, logger="nova"):
        result = router.synthesize("Hola", Identity.ASTI)

    assert result.success
    assert result.value.provider == "local"
    assert "TTS_FAILED" in caplog.text


def test_online_failure_blocks_online_for_a_while():
    clock = FakeClock()
    online = FakeTTS("online", fail=True)
    router, local = create_router(
        online=online,
        prefer_online=True,
        clock=clock,
    )

    router.synthesize("Uno", Identity.ASTI)
    router.synthesize("Dos", Identity.ASTI)

    assert len(online.calls) == 1
    assert len(local.calls) == 2

    clock.now = 61.0
    router.synthesize("Tres", Identity.ASTI)

    assert len(online.calls) == 2


def test_identity_and_text_reach_the_provider():
    router, local = create_router()

    router.synthesize("Buenos días, Jefe", Identity.ATLAS)

    assert local.calls == [("Buenos días, Jefe", Identity.ATLAS)]


def test_local_failure_is_returned_as_failure():
    local = FakeTTS("local", fail=True)
    router = TTSRouter(local=local)

    result = router.synthesize("Hola", Identity.ATLAS)

    assert not result.success
    assert result.error.code == "TTS_FAILED"


def test_spoken_text_is_never_logged(caplog):
    online = FakeTTS("online", fail=True)
    router, _ = create_router(online=online, prefer_online=True)

    with caplog.at_level(logging.DEBUG, logger="nova"):
        router.synthesize("secreto-123", Identity.ASTI)

    assert "secreto-123" not in caplog.text