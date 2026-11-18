from pathlib import Path

from nova.automation import AutomationCommandHandler, AutomationService
from nova.automation.files import FileService
from nova.security import SecurityService
from nova.storage import StorageService


class FakeProvider:
    def __init__(self):
        self.calls = []

    def find_program(self, name):
        return None

    def open_path(self, target):
        self.calls.append(("path", target))

    def open_url(self, url):
        self.calls.append(("url", url))

    def media(self, command):
        self.calls.append(("media", command))


def make(tmp_path, monkeypatch):
    for name in ("Downloads", "Documents"):
        (tmp_path / name).mkdir()

    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    storage = StorageService(tmp_path / "t.db")
    storage.initialize()
    provider, recycled = FakeProvider(), []

    def recycle(path):
        recycled.append(path)
        Path(path).unlink()

    security = SecurityService(storage.permission_repository)
    service = AutomationService(security, provider, FileService(security, recycle))

    return storage, provider, recycled, AutomationCommandHandler(service)


def test_create_folder_no_confirmation(tmp_path, monkeypatch):
    storage, _, _, handler = make(tmp_path, monkeypatch)

    assert "Carpeta creada" in handler.reply_to(
        "crea una carpeta Proyectos en documentos"
    )
    assert (tmp_path / "Documents" / "Proyectos").is_dir()
    assert "no es válido" in handler.reply_to("crea una carpeta ..\\x en documentos")
    storage.close()


def test_move_needs_confirmation_and_never_overwrites(tmp_path, monkeypatch):
    storage, _, _, handler = make(tmp_path, monkeypatch)
    (tmp_path / "Downloads" / "informe.pdf").write_text("a")

    assert "¿Confirmas?" in handler.reply_to("mueve informe de descargas a documentos")
    assert (tmp_path / "Downloads" / "informe.pdf").exists()
    assert "Movido" in handler.reply_to("sí")
    assert (tmp_path / "Documents" / "informe.pdf").exists()

    (tmp_path / "Downloads" / "informe.pdf").write_text("b")
    assert "no sobrescribo" in handler.reply_to("mueve informe de descargas a documentos")
    storage.close()


def test_copy_is_free_and_no_overwrite(tmp_path, monkeypatch):
    storage, _, _, handler = make(tmp_path, monkeypatch)
    (tmp_path / "Downloads" / "a.txt").write_text("x")

    assert "Copiado" in handler.reply_to("copia a.txt de descargas a documentos")
    assert (tmp_path / "Downloads" / "a.txt").exists()
    assert "no sobrescribo" in handler.reply_to("copia a.txt de descargas a documentos")
    storage.close()


def test_delete_goes_to_recycler_only_after_yes(tmp_path, monkeypatch):
    storage, _, recycled, handler = make(tmp_path, monkeypatch)
    target = tmp_path / "Downloads" / "viejo.txt"
    target.write_text("x")

    handler.reply_to("borra viejo de descargas")
    assert "No lo haré" in handler.reply_to("no")
    assert recycled == [] and target.exists()

    handler.reply_to("elimina viejo de descargas")
    assert "papelera" in handler.reply_to("sí")
    assert recycled == [str(target)]
    storage.close()


def test_organize_shows_plan_then_moves(tmp_path, monkeypatch):
    storage, _, _, handler = make(tmp_path, monkeypatch)
    downloads = tmp_path / "Downloads"

    for name in ("a.jpg", "b.pdf", "c.xyz"):
        (downloads / name).write_text("x")

    assert "2 archivos" in handler.reply_to("organiza descargas")
    assert "Organizados 2" in handler.reply_to("sí")
    assert (downloads / "Imágenes" / "a.jpg").exists()
    assert (downloads / "Documentos" / "b.pdf").exists()
    assert (downloads / "c.xyz").exists()
    storage.close()


def test_out_of_scope_blocked(tmp_path, monkeypatch):
    storage, _, recycled, handler = make(tmp_path, monkeypatch)

    reply = handler.reply_to("borra secreto de C:\\Windows")

    assert "No toco carpetas del sistema" in reply
    assert recycled == []
    storage.close()


def test_search_list_and_open_result(tmp_path, monkeypatch):
    storage, provider, _, handler = make(tmp_path, monkeypatch)
    sub = tmp_path / "Documents" / "sub"
    sub.mkdir()
    (sub / "informe_final.pdf").write_text("x")

    assert "informe_final.pdf" in handler.reply_to("busca el archivo informe")
    assert "Abriendo" in handler.reply_to("abre el 1")
    assert provider.calls == [("path", str(sub / "informe_final.pdf"))]
    assert "sub/" in handler.reply_to("qué hay en documentos")
    storage.close()