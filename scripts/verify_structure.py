from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


REQUIRED_PATHS = [
    "config",
    "data",
    "data/backups",
    "data/cache",
    "data/database",
    "data/logs",
    "docs",
    "models",
    "scripts",
    "src/nova",
    "src/nova/ai",
    "src/nova/automation",
    "src/nova/core",
    "src/nova/memory",
    "src/nova/plugins",
    "src/nova/security",
    "src/nova/storage",
    "src/nova/ui",
    "src/nova/ui/main",
    "src/nova/ui/orb",
    "src/nova/voice",
    "tests",
    "tests/unit",
    "tests/integration",
]


def main() -> int:
    missing = []

    for relative_path in REQUIRED_PATHS:
        path = ROOT / relative_path

        if not path.exists():
            missing.append(relative_path)

    if missing:
        print("❌ Faltan rutas:")

        for path in missing:
            print(f"  - {path}")

        return 1

    print("✅ Estructura de NOVA correcta.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())