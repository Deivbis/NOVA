from pathlib import Path
import sys

from nova.config.loader import ConfigLoader


def main() -> int:
    config_path = Path("config/default.toml")

    try:
        config = ConfigLoader().load(config_path)
    except Exception as exc:
        print(f"❌ Configuración inválida: {exc}")
        return 1

    checks = [
        ("Nombre", config.nova.name == "NOVA"),
        ("Versión", bool(config.nova.version)),
        ("Idioma", config.nova.language == "es"),
        ("Modo offline", config.connectivity.offline_mode_allowed),
        ("Orbe", config.ui.orb.enabled),
        ("Configuración de voz", config.voice.enabled is False),
    ]

    failed = False

    for name, result in checks:
        if result:
            print(f"✅ {name}")
        else:
            print(f"❌ {name}")
            failed = True

    if failed:
        print("❌ Verificación de configuración fallida.")
        return 1

    print("✅ Configuración de NOVA correcta.")
    return 0


if __name__ == "__main__":
    sys.exit(main())