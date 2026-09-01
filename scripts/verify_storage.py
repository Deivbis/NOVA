from pathlib import Path
import tempfile

from nova.storage.service import StorageService


def main() -> None:
    with tempfile.TemporaryDirectory() as directory:
        database_path = (
            Path(directory)
            / "database"
            / "nova.db"
        )

        storage = StorageService(database_path)

        storage.initialize()

        if not database_path.exists():
            raise RuntimeError(
                "❌ Database was not created."
            )

        if not storage.manager.database.health_check():
            raise RuntimeError(
                "❌ Database integrity check failed."
            )

        journal_mode = (
            storage.manager.database.journal_mode()
        )

        if journal_mode.lower() != "wal":
            raise RuntimeError(
                f"❌ WAL is not enabled: {journal_mode}"
            )

        storage.set_system_value(
            "verification",
            "ok",
        )

        value = storage.get_system_value(
            "verification"
        )

        if value != "ok":
            raise RuntimeError(
                "❌ Persistence test failed."
            )

        storage.close()

    print("✅ Storage de NOVA correcto.")


if __name__ == "__main__":
    main()