"""Acciones reales del sistema (Windows). Sustituible por otro Provider."""

import os
import webbrowser
from pathlib import Path
from typing import Protocol

from nova.memory.text import normalize

_BUILTIN_PROGRAMS = {
    "calculadora": ("Calculadora", "calc.exe"),
    "bloc de notas": ("Bloc de notas", "notepad.exe"),
    "paint": ("Paint", "mspaint.exe"),
    "explorador": ("Explorador de archivos", "explorer.exe"),
    "explorador de archivos": ("Explorador de archivos", "explorer.exe"),
}

_MEDIA_KEYS = {
    "play_pause": (0xB3, 1),
    "next": (0xB0, 1),
    "previous": (0xB1, 1),
    "volume_up": (0xAF, 5),
    "volume_down": (0xAE, 5),
    "mute": (0xAD, 1),
}


class SystemProvider(Protocol):
    def find_program(self, name: str) -> tuple[str, str, bool] | None: ...

    def open_path(self, target: str) -> None: ...

    def open_url(self, url: str) -> None: ...

    def media(self, command: str) -> None: ...


class WindowsSystemProvider:
    def find_program(self, name: str) -> tuple[str, str, bool] | None:
        """(nombre, destino, es_básico). Busca en el menú Inicio."""
        query = normalize(name).strip()

        if query in _BUILTIN_PROGRAMS:
            label, target = _BUILTIN_PROGRAMS[query]
            return label, target, True

        if not query:
            return None

        best: tuple[int, Path] | None = None

        for root in self._roots():
            try:
                shortcuts = list(root.rglob("*.lnk"))
            except OSError:
                continue

            for path in shortcuts:
                stem = normalize(path.stem)

                if "uninstall" in stem or "desinstal" in stem:
                    continue

                if stem == query:
                    return path.stem, str(path), False

                if query in stem and (best is None or len(stem) < best[0]):
                    best = (len(stem), path)

        if best is None:
            return None

        return best[1].stem, str(best[1]), False

    def open_path(self, target: str) -> None:
        os.startfile(target)  # type: ignore[attr-defined]

    def open_url(self, url: str) -> None:
        webbrowser.open(url)

    def media(self, command: str) -> None:
        import ctypes

        key, repeat = _MEDIA_KEYS[command]
        user32 = ctypes.windll.user32  # type: ignore[attr-defined]

        for _ in range(repeat):
            user32.keybd_event(key, 0, 0, 0)
            user32.keybd_event(key, 0, 2, 0)

    @staticmethod
    def _roots() -> list[Path]:
        suffix = Path("Microsoft/Windows/Start Menu/Programs")
        bases = (os.environ.get("ProgramData"), os.environ.get("APPDATA"))

        return [
            Path(base) / suffix
            for base in bases
            if base and (Path(base) / suffix).is_dir()
        ]