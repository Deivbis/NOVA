"""Cambia las preferencias de voz sin abrir la app (v0.3).

Ejecutar desde C:\\NOVA, combinando opciones:
  python scripts/set_voice.py on atlas local
  python scripts/set_voice.py off
  python scripts/set_voice.py asti online
  python scripts/set_voice.py "vocab=Deivbis,Atlas,Asti,NOVA"
  python scripts/set_voice.py show

El vocabulario ayuda al reconocimiento con nombres propios; ponlo entre
comillas para que PowerShell no separe las comas.
"""

import dataclasses
import sys

from nova.core import Identity
from nova.storage.paths import default_settings_path
from nova.voice import load_voice_settings, save_voice_settings


def main() -> int:
    settings = load_voice_settings()
    changed = False

    for argument in sys.argv[1:]:
        option = argument.lower()

        if option == "on":
            settings = dataclasses.replace(settings, enabled=True)
        elif option == "off":
            settings = dataclasses.replace(settings, enabled=False)
        elif option in ("atlas", "asti"):
            settings = dataclasses.replace(
                settings,
                identity=Identity(option),
            )
        elif option == "online":
            settings = dataclasses.replace(settings, prefer_online=True)
        elif option == "local":
            settings = dataclasses.replace(settings, prefer_online=False)
        elif option.startswith("vocab="):
            words = tuple(
                word.strip()
                for word in argument[6:].split(",")
                if word.strip()
            )

            if not words:
                print("El vocabulario no puede estar vacío.")
                return 1

            settings = dataclasses.replace(settings, vocabulary=words)
        elif option == "show":
            continue
        else:
            print(f"Opción desconocida: {argument}")
            return 1

        changed = True

    if changed:
        save_voice_settings(settings)

    print(f"Archivo: {default_settings_path()}")
    print(settings)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())