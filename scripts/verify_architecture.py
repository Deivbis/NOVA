from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = [
    "src/nova/core/__init__.py",
    "src/nova/core/capabilities.py",
    "src/nova/core/commands.py",
    "src/nova/core/events.py",
    "src/nova/core/exceptions.py",
    "src/nova/core/orchestrator.py",
    "src/nova/core/result.py",
    "src/nova/core/services.py",
    "src/nova/core/state.py",
    "src/nova/ui/qml/Main.qml",
    "src/nova/ui/qml/components/qmldir",
    "docs/NOVA-ARCH-001-ARQUITECTURA-BASE.md",
    "docs/NOVA-ARCH-002-RESPONSABILIDADES-MODULOS.md",
    "docs/NOVA-ARCH-003-ESTADOS.md",
    "docs/NOVA-ARCH-004-ORBE-INTEGRACION.md",
]


def main() -> int:
    missing = []

    for relative_path in REQUIRED_FILES:
        path = ROOT / relative_path

        if not path.is_file():
            missing.append(relative_path)

    if missing:
        print("❌ Faltan archivos arquitectónicos:")

        for path in missing:
            print(f"  - {path}")

        return 1

    print("✅ Arquitectura base de NOVA presente.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())