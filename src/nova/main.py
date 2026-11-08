from pathlib import Path

from nova.config import ConfigurationService
from nova.core import ConnectivityState, CoreOrchestrator
from nova.core.logging_setup import get_logger, setup_logging
from nova.storage import StorageService

logger = get_logger(__name__)


def create_configuration() -> ConfigurationService:
    """Create the NOVA configuration service."""
    config_path = Path("config/default.toml")

    return ConfigurationService(config_path)


def create_core() -> CoreOrchestrator:
    """Create and initialize the NOVA core."""
    core = CoreOrchestrator()

    core.start()
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

    setup_logging(
        Path(config.paths.logs),
        debug=config.execution.debug,
    )
    logger.info(
        "NOVA %s iniciando (entorno: %s).",
        config.nova.version,
        config.nova.environment,
    )

    core = create_core()

    storage = create_storage()

    try:
        storage.initialize()
        logger.info("Almacenamiento inicializado.")

        print(f"Configuración: {config.nova.name} {config.nova.version}")
        print(f"Estado: {core.state.value}")
        print(f"Conectividad: {core.connectivity.value}")
        print("Almacenamiento: SQLite operativo")

    except Exception:
        logger.exception("Fallo durante el arranque de NOVA.")
        storage.close()
        raise

    finally:
        storage.close()
        core.stop()


if __name__ == "__main__":
    main()