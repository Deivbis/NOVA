"""Demo de personalidad (v0.4): las mismas frases con Atlas y con Asti.

Ejecutar desde C:\\NOVA con Ollama abierto:
  python scripts/demo_personality.py

Para juzgar el tono a mano: sin emojis, breve, trato "Jefe", sin fingir
acciones y con el género correcto.
"""

import time

from nova.ai import LocalAIService
from nova.core import Identity
from nova.personality import build_messages

PHRASES = [
    "Hola",
    "¿Qué hora es?",
    "Abre el navegador y busca música para programar",
    "Estoy cansado, llevo horas programando",
    "Explícame qué es una API",
    "Tengo una reunión mañana y no he preparado nada",
    "Cuéntame un chiste",
]


def main() -> None:
    service = LocalAIService()

    for identity in (Identity.ATLAS, Identity.ASTI):
        print(f"\n=== {identity.value.upper()} ===")

        for phrase in PHRASES:
            messages = build_messages(
                identity,
                [{"role": "user", "content": phrase}],
            )

            start = time.perf_counter()
            result = service.chat(messages)
            elapsed = time.perf_counter() - start

            print(f"\n> {phrase}")

            if result.success:
                print(f"({elapsed:.1f}s) {result.value}")
            else:
                print(f"ERROR {result.error.code}: {result.error.message}")


if __name__ == "__main__":
    main()