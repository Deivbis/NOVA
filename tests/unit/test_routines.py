from nova.automation import (
    AutomationCommandHandler,
    AutomationService,
    RoutineHandler,
)
from nova.security import SecurityService
from nova.storage import StorageService


class FakeProvider:
    def __init__(self):
        self.calls = []

    def find_program(self, name):
        if "spotify" in name.lower():
            return "Spotify", r"C:\spotify.lnk", False

        return None

    def open_path(self, target):
        self.calls.append(("path", target))

    def open_url(self, url):
        self.calls.append(("url", url))

    def media(self, command):
        self.calls.append(("media", command))


def make(tmp_path):
    storage = StorageService(tmp_path / "t.db")
    storage.initialize()
    provider = FakeProvider()
    service = AutomationService(
        SecurityService(storage.permission_repository), provider
    )
    automation = AutomationCommandHandler(service)

    return storage, provider, RoutineHandler(
        storage.routine_repository, automation, service
    )


def test_create_and_run(tmp_path):
    storage, provider, routines = make(tmp_path)

    assert "creada" in routines.reply_to(
        "crea la rutina modo trabajo: abre youtube, sube el volumen"
    )
    assert "Rutina completada" in routines.reply_to("modo trabajo")
    assert provider.calls == [
        ("url", "https://www.youtube.com"),
        ("media", "volume_up"),
    ]
    storage.close()


def test_invalid_steps_rejected(tmp_path):
    storage, _, routines = make(tmp_path)

    assert "zzz" in routines.reply_to("crea la rutina x: abre zzz")
    assert "No puedo usar" in routines.reply_to(
        "crea la rutina y: borra a de descargas"
    )
    assert routines.reply_to("x") is None
    storage.close()


def test_pauses_for_confirmation_then_continues(tmp_path):
    storage, provider, routines = make(tmp_path)

    routines.reply_to("crea la rutina estudio: abre spotify, abre youtube")
    assert "¿lo permito?" in routines.reply_to("estudio")
    assert provider.calls == []
    assert "Rutina completada" in routines.reply_to("sí")
    assert provider.calls == [
        ("path", r"C:\spotify.lnk"),
        ("url", "https://www.youtube.com"),
    ]
    storage.close()


def test_other_text_stops_routine_and_delete(tmp_path):
    storage, provider, routines = make(tmp_path)

    routines.reply_to("crea la rutina estudio: abre spotify, abre youtube")
    routines.reply_to("estudio")
    assert "detenida" in routines.reply_to("cuéntame un chiste")
    assert "borrada" in routines.reply_to("borra la rutina estudio")
    assert routines.reply_to("estudio") is None
    storage.close()