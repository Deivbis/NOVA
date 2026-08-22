from nova.core import ConnectivityState, CoreOrchestrator, NovaState


def create_core() -> CoreOrchestrator:
    core = CoreOrchestrator()

    core.set_state(NovaState.IDLE)
    core.set_connectivity(ConnectivityState.UNKNOWN)

    return core


def main() -> None:
    print("NOVA – Personal Intelligence Platform")
    print("NOVA está iniciando...")

    core = create_core()

    print(f"Estado: {core.state.value}")
    print(f"Conectividad: {core.connectivity.value}")


if __name__ == "__main__":
    main()