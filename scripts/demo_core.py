"""Demostración v0.1: Command -> Core -> Service -> Result -> Event.

No requiere UI, Internet ni IA (DOC-023).
Ejecutar desde C:\\NOVA:  python scripts/demo_core.py
"""

from pathlib import Path

from nova.core import Command, CoreOrchestrator, SystemService
from nova.core.logging_setup import setup_logging


def main() -> None:
    setup_logging(Path("data/logs"), debug=True)

    core = CoreOrchestrator()
    SystemService(core).register()
    core.subscribe(
        lambda event: print(f"   [evento] {event.name}: {event.payload}")
    )

    print("1) Iniciando el Core...")
    core.start()

    print("2) Enviando el comando system.ping...")
    result = core.dispatch(Command(name=SystemService.PING, source="demo"))
    print(f"   Resultado: éxito={result.success}, valor={result.value!r}")

    print("3) Comando que requiere Internet, sin conexión...")
    result = core.dispatch(
        Command(
            name=SystemService.PING,
            requires_internet=True,
            source="demo",
        )
    )
    print(f"   Resultado: éxito={result.success}, error={result.error}")

    print("4) Consultando el estado del sistema...")
    result = core.dispatch(Command(name=SystemService.STATUS, source="demo"))
    print(f"   Estado: {result.value}")

    print("5) Deteniendo el Core...")
    core.stop()


if __name__ == "__main__":
    main()