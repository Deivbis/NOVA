from pathlib import Path

from nova.automation import (
    AutomationCommandHandler,
    AutomationService,
    parse_automation_command,
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
    security = SecurityService(storage.permission_repository)
    handler = AutomationCommandHandler(AutomationService(security, provider))

    return storage, provider, handler


def test_parse():
    assert parse_automation_command("hola") is None
    assert parse_automation_command("pausa la música").media == "play_pause"
    assert parse_automation_command("abre la carpeta de descargas").hint == "folder"


def test_builtin_web_and_media_need_no_confirmation(tmp_path):
    storage, provider, handler = make(tmp_path)

    handler.reply_to("abre youtube")
    handler.reply_to("sube el volumen")

    assert provider.calls == [
        ("url", "https://www.youtube.com"),
        ("media", "volume_up"),
    ]
    storage.close()


def test_first_use_confirm_then_free(tmp_path):
    storage, provider, handler = make(tmp_path)

    assert "¿lo permito?" in handler.reply_to("abre spotify")
    assert provider.calls == []
    assert "Permiso guardado" in handler.reply_to("Sí, hazlo")
    assert provider.calls == [("path", r"C:\spotify.lnk")]

    handler.reply_to("abre spotify")
    assert len(provider.calls) == 2
    storage.close()


def test_no_cancels_and_other_text_drops_request(tmp_path):
    storage, provider, handler = make(tmp_path)

    handler.reply_to("abre spotify")
    assert "No lo haré" in handler.reply_to("no")

    handler.reply_to("abre spotify")
    assert handler.reply_to("cuéntame un chiste") is None
    assert handler.reply_to("sí") is None
    assert provider.calls == []
    storage.close()


def test_revoke_asks_again(tmp_path):
    storage, provider, handler = make(tmp_path)

    handler.reply_to("abre spotify")
    handler.reply_to("sí")

    assert "revocado" in handler.reply_to("revoca el permiso de spotify")
    assert "¿lo permito?" in handler.reply_to("abre spotify")
    storage.close()


def test_blocks_bad_targets(tmp_path):
    storage, provider, handler = make(tmp_path)

    handler.reply_to("abre la web file://c/secreto")
    handler.reply_to("abre javascript:alert(1)")
    handler.reply_to(r"abre la carpeta \\servidor\datos")

    assert provider.calls == []
    storage.close()


def test_folder_alias(tmp_path, monkeypatch):
    (tmp_path / "Downloads").mkdir()
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    storage, provider, handler = make(tmp_path)

    handler.reply_to("abre descargas")

    assert provider.calls == [("path", str(tmp_path / "Downloads"))]
    storage.close()