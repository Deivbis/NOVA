from pathlib import Path

from nova.config import ConfigurationService
from nova.core import ConnectivityState, CoreOrchestrator, SystemService
from nova.core.logging_setup import get_logger, setup_logging
from nova.storage import StorageService
from nova.storage.paths import (
    default_data_dir,
    default_database_path,
    default_logs_dir,
)

logger = get_logger(__name__)

# src/nova/main.py -> raíz del proyecto (no depende del directorio actual).
PROJECT_ROOT = Path(__file__).resolve().parents[2]


def create_configuration() -> ConfigurationService:
    """Create the NOVA configuration service."""
    config_path = PROJECT_ROOT / "config" / "default.toml"

    return ConfigurationService(config_path)


def create_core() -> CoreOrchestrator:
    """Create, populate and start the NOVA core."""
    core = CoreOrchestrator()

    SystemService(core).register()
    core.start()
    core.set_connectivity(ConnectivityState.UNKNOWN)

    return core


def create_storage() -> StorageService:
    """Create the NOVA storage service."""
    return StorageService(default_database_path())


def main() -> None:
    """Application entry point."""
    print("NOVA – Personal Intelligence Platform")
    print("NOVA está iniciando...")

    configuration = create_configuration()
    config = configuration.initialize()

    setup_logging(
        default_logs_dir(),
        debug=config.execution.debug,
    )
    logger.info(
        "NOVA %s iniciando (entorno: %s).",
        config.nova.version,
        config.nova.environment,
    )
    logger.debug("Directorio de datos: %s", default_data_dir())

    core = create_core()
    storage = create_storage()

    try:
        storage.initialize()
        logger.info("Almacenamiento inicializado.")

        capabilities = ", ".join(
            item.id for item in core.capabilities.list_capabilities()
        )

        print(f"Configuración: {config.nova.name} {config.nova.version}")
        print(f"Estado: {core.state.value}")
        print(f"Conectividad: {core.connectivity.value}")
        print(f"Capacidades: {capabilities}")
        print(f"Datos: {default_data_dir()}")
        print("Almacenamiento: SQLite operativo")

    except Exception:
        logger.exception("Fallo durante el arranque de NOVA.")
        raise

    finally:
        storage.close()
        core.stop()


if __name__ == "__main__":
    main()