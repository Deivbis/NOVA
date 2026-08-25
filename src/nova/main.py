from pathlib import Path

from nova.config import ConfigurationService
from nova.core import ConnectivityState, CoreOrchestrator, NovaState


def create_configuration() -> ConfigurationService:
    config_path = Path("config/default.toml")

    return ConfigurationService(config_path)


def create_core() -> CoreOrchestrator:
    core = CoreOrchestrator()

    core.set_state(NovaState.IDLE)
    core.set_connectivity(ConnectivityState.UNKNOWN)

    return core


def main() -> None:
    print("NOVA – Personal Intelligence Platform")
    print("NOVA está iniciando...")

    configuration = create_configuration()
    config = configuration.initialize()

    core = create_core()

    print(f"Configuración: {config.nova.name} {config.nova.version}")
    print(f"Estado: {core.state.value}")
    print(f"Conectividad: {core.connectivity.value}")


if __name__ == "__main__":
    main()