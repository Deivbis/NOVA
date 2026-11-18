"""Operaciones de archivos con alcance limitado (SPEC-007, D-032)."""

import os
import re
import shutil
from collections.abc import Callable
from pathlib import Path

from nova.automation.commands import (
    FOLDER_ALIASES,
    AutomationAction,
    AutomationCommand,
)
from nova.core.automation import FileOperation, FileOpKind
from nova.core.logging_setup import get_logger
from nova.core.result import Result
from nova.memory.text import normalize
from nova.security import SecurityService

logger = get_logger(__name__)

MAX_RESULTS = 10
MAX_LIST = 15
MAX_SCAN = 20000
MAX_DEPTH = 6
MAX_ORGANIZE = 500

_DRIVE = re.compile(r"^[A-Za-z]:[\\/]")
_BAD_NAME = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
_CATEGORIES = {
    "Imágenes": {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".svg"},
    "Documentos": {".pdf", ".doc", ".docx", ".txt", ".xls", ".xlsx",
                   ".ppt", ".pptx", ".csv", ".md"},
    "Música": {".mp3", ".wav", ".flac", ".m4a", ".ogg"},
    "Videos": {".mp4", ".mkv", ".avi", ".mov", ".webm"},
    "Comprimidos": {".zip", ".rar", ".7z", ".tar", ".gz"},
    "Instaladores": {".exe", ".msi"},
}


def recycle_to_bin(path: str) -> None:
    """Envía a la papelera de Windows (recuperable)."""
    import ctypes
    from ctypes import wintypes

    class SHFILEOPSTRUCTW(ctypes.Structure):
        _fields_ = [
            ("hwnd", wintypes.HWND), ("wFunc", wintypes.UINT),
            ("pFrom", wintypes.LPCWSTR), ("pTo", wintypes.LPCWSTR),
            ("fFlags", ctypes.c_ushort),
            ("fAnyOperationsAborted", wintypes.BOOL),
            ("hNameMappings", ctypes.c_void_p),
            ("lpszProgressTitle", wintypes.LPCWSTR),
        ]

    # FO_DELETE | ALLOWUNDO | NOCONFIRMATION | SILENT | NOERRORUI
    op = SHFILEOPSTRUCTW(
        None, 3, path + "\0", None, 0x40 | 0x10 | 0x4 | 0x400, False, None, None
    )
    code = ctypes.windll.shell32.SHFileOperationW(ctypes.byref(op))

    if code != 0 or op.fAnyOperationsAborted:
        raise OSError("No se pudo enviar a la papelera.")


def _category(path: Path) -> str | None:
    suffix = path.suffix.lower()

    for folder, extensions in _CATEGORIES.items():
        if suffix in extensions:
            return folder

    return None


class FileService:
    def __init__(
        self,
        security: SecurityService,
        recycler: Callable[[str], None] = recycle_to_bin,
    ) -> None:
        self._security = security
        self._recycler = recycler

    def resolve_location(self, text: str) -> Result[Path]:
        text = text.strip().strip("\"'")
        alias = FOLDER_ALIASES.get(normalize(text))

        if alias:
            path = Path.home() / alias
        elif _DRIVE.match(text):
            path = Path(text)
        else:
            return Result.fail(
                "FILES_UNKNOWN_LOCATION",
                "No conozco esa ubicación. Usa una carpeta como descargas "
                "o una ruta completa.",
            )

        reason = self._security.scope_error(path)

        if reason:
            return Result.fail("FILES_OUT_OF_SCOPE", reason)

        resolved = path.resolve()

        if not resolved.is_dir():
            return Result.fail("FILES_NOT_FOUND", "Esa carpeta no existe.")

        return Result.ok(resolved)

    def search(
        self,
        name: str,
        location: str | None = None,
    ) -> Result[list[Path]]:
        needle = normalize(name).strip()

        if not needle:
            return Result.fail("FILES_INVALID", "Dime qué archivo buscar.")

        if location:
            located = self.resolve_location(location)

            if not located.success:
                return located

            roots = [located.value]
        else:
            roots = [r for r in self._security.allowed_roots() if r.is_dir()]

        found: list[Path] = []
        scanned = 0

        for root in roots:
            base = len(root.parts)

            for dirpath, dirnames, filenames in os.walk(root):
                if len(Path(dirpath).parts) - base >= MAX_DEPTH:
                    dirnames.clear()

                for entry in (*dirnames, *filenames):
                    scanned += 1

                    if scanned > MAX_SCAN:
                        return Result.ok(found)

                    path = Path(dirpath) / entry

                    if needle in normalize(entry) and path not in found:
                        found.append(path)

                        if len(found) >= MAX_RESULTS:
                            return Result.ok(found)

        return Result.ok(found)

    def list_dir(self, location: str) -> Result[tuple[Path, list[str], int]]:
        located = self.resolve_location(location)

        if not located.success:
            return located

        try:
            entries = sorted(
                located.value.iterdir(),
                key=lambda p: (not p.is_dir(), p.name.lower()),
            )
        except OSError:
            return Result.fail("FILES_IO", "No pude leer esa carpeta.")

        names = [e.name + ("/" if e.is_dir() else "") for e in entries]

        return Result.ok(
            (located.value, names[:MAX_LIST], max(0, len(names) - MAX_LIST))
        )

    def plan(self, command: AutomationCommand) -> Result[FileOperation]:
        action = command.action

        if action == AutomationAction.ORGANIZE:
            return self._organize(command.source)

        located = self.resolve_location(command.source)

        if not located.success:
            return located

        folder = located.value

        if action == AutomationAction.CREATE_DIR:
            return self._create(folder, command.name)

        if action == AutomationAction.RENAME:
            return self._rename(folder, command.name, command.dest)

        found = self._find(folder, command.name)

        if not found.success:
            return found

        source = found.value

        if action == AutomationAction.DELETE:
            return Result.ok(FileOperation(
                FileOpKind.DELETE,
                f"mandar a la papelera {source.name} de {folder.name}",
                source=str(source),
            ))

        return self._copy_move(command, folder, source)

    def execute(self, op: FileOperation) -> Result[int]:
        try:
            if op.kind == FileOpKind.ORGANIZE:
                return Result.ok(self._do_organize(op))

            dest = Path(op.dest) if op.dest else None

            if op.kind != FileOpKind.DELETE and dest.exists():
                return Result.fail(
                    "FILES_EXISTS", "Ya existe ese destino; no sobrescribo."
                )

            if op.kind == FileOpKind.CREATE_DIR:
                dest.mkdir()
            elif op.kind == FileOpKind.COPY:
                source = Path(op.source)
                (shutil.copytree if source.is_dir() else shutil.copy2)(
                    source, dest
                )
            elif op.kind in (FileOpKind.MOVE, FileOpKind.RENAME):
                shutil.move(op.source, dest)
            else:
                self._recycler(op.source)
        except (OSError, shutil.Error) as exc:
            logger.warning(
                "Fallo de archivos (%s): %s", op.kind.value, type(exc).__name__
            )
            return Result.fail("FILES_IO", "No pude completar la operación.")

        return Result.ok(1)

    def _do_organize(self, op: FileOperation) -> int:
        moved = 0

        for source, dest in op.moves:
            target = Path(dest)

            if target.exists() or not Path(source).is_file():
                continue

            target.parent.mkdir(exist_ok=True)
            shutil.move(source, target)
            moved += 1

        return moved

    def _create(self, folder: Path, name: str) -> Result[FileOperation]:
        valid = self._name(name)

        if not valid.success:
            return valid

        dest = folder / valid.value

        if dest.exists():
            return Result.fail("FILES_EXISTS", "Ya existe algo con ese nombre.")

        return Result.ok(FileOperation(
            FileOpKind.CREATE_DIR,
            f"crear la carpeta {valid.value} en {folder.name}",
            dest=str(dest),
        ))

    def _rename(
        self, folder: Path, name: str, new: str
    ) -> Result[FileOperation]:
        found = self._find(folder, name)
        valid = self._name(new)

        if not found.success:
            return found

        if not valid.success:
            return valid

        dest = folder / valid.value

        if dest.exists():
            return Result.fail("FILES_EXISTS", "Ya existe algo con ese nombre.")

        return Result.ok(FileOperation(
            FileOpKind.RENAME,
            f"renombrar {found.value.name} como {valid.value}",
            source=str(found.value), dest=str(dest),
        ))

    def _copy_move(
        self, command: AutomationCommand, folder: Path, source: Path
    ) -> Result[FileOperation]:
        target = self.resolve_location(command.dest)

        if not target.success:
            return target

        dest = target.value / source.name

        if dest.exists():
            return Result.fail(
                "FILES_EXISTS", "Ya existe en el destino; no sobrescribo nada."
            )

        if source.is_dir() and str(dest).startswith(str(source) + os.sep):
            return Result.fail(
                "FILES_INVALID", "No puedo meter una carpeta dentro de sí misma."
            )

        move = command.action == AutomationAction.MOVE

        return Result.ok(FileOperation(
            FileOpKind.MOVE if move else FileOpKind.COPY,
            f"{'mover' if move else 'copiar'} {source.name} de "
            f"{folder.name} a {target.value.name}",
            source=str(source), dest=str(dest),
        ))

    def _organize(self, location: str) -> Result[FileOperation]:
        located = self.resolve_location(location)

        if not located.success:
            return located

        folder = located.value
        moves: list[tuple[str, str]] = []
        counts: dict[str, int] = {}

        try:
            entries = sorted(folder.iterdir())
        except OSError:
            return Result.fail("FILES_IO", "No pude leer esa carpeta.")

        for entry in entries:
            category = _category(entry)

            if (
                category is None
                or entry.name.startswith(".")
                or not entry.is_file()
                or (folder / category / entry.name).exists()
            ):
                continue

            moves.append((str(entry), str(folder / category / entry.name)))
            counts[category] = counts.get(category, 0) + 1

            if len(moves) >= MAX_ORGANIZE:
                break

        if not moves:
            return Result.fail("FILES_NOTHING", "No hay nada que organizar ahí.")

        summary = ", ".join(f"{c} {n}" for c, n in counts.items())

        return Result.ok(FileOperation(
            FileOpKind.ORGANIZE,
            f"organizar {folder.name}: {len(moves)} archivos ({summary})",
            source=str(folder), moves=tuple(moves),
        ))

    def _find(self, folder: Path, name: str) -> Result[Path]:
        needle = normalize(name.strip().strip("\"'")).strip()

        try:
            entries = list(folder.iterdir())
        except OSError:
            return Result.fail("FILES_IO", "No pude leer esa carpeta.")

        exact = [p for p in entries if normalize(p.name) == needle]
        partial = exact or [p for p in entries if needle and needle in normalize(p.name)]

        if len(partial) == 1:
            return Result.ok(partial[0])

        if not partial:
            return Result.fail(
                "FILES_NOT_FOUND", f"No encontré «{name}» en {folder.name}."
            )

        names = ", ".join(p.name for p in partial[:5])

        return Result.fail(
            "FILES_AMBIGUOUS", f"Hay varios ({names}). Sé más específico."
        )

    @staticmethod
    def _name(text: str) -> Result[str]:
        cleaned = text.strip().strip("\"'").strip()

        if (
            not cleaned
            or len(cleaned) > 150
            or cleaned.endswith(".")
            or _BAD_NAME.search(cleaned)
        ):
            return Result.fail("FILES_INVALID", "Ese nombre no es válido.")

        return Result.ok(cleaned)