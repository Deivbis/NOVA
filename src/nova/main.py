from pathlib import Path

from nova.config import ConfigurationService
from nova.core import ConnectivityState, CoreOrchestrator, NovaState
from nova.storage import StorageService


def create_configuration() -> ConfigurationService:
    """Create the NOVA configuration service."""
    config_path = Path("config/default.toml")

    return ConfigurationService(config_path)


def create_core() -> CoreOrchestrator:
    """Create and initialize the NOVA core."""
    core = CoreOrchestrator()

    core.set_state(NovaState.IDLE)
    core.set_connectivity(ConnectivityState.UNKNOWN)

    return core


def create_storage() -> StorageService:
    """Create the NOVA storage service."""
    database_path = Path("data/database/nova.db")

    return StorageService(database_path)


def main() -> None:
    """Application entry point."""
    print("NOVA – Personal Intelligence Platform")
    print("NOVA está iniciando...")

    configuration = create_configuration()
    config = configuration.initialize()

    core = create_core()

    storage = create_storage()

    try:
        storage.initialize()

        print(f"Configuración: {config.nova.name} {config.nova.version}")
        print(f"Estado: {core.state.value}")
        print(f"Conectividad: {core.connectivity.value}")
        print("Almacenamiento: SQLite operativo")

    except Exception:
        storage.close()
        raise

    finally:
        storage.close()


if __name__ == "__main__":
    main()