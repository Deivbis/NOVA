"""Demo de voz (v0.3): sintetiza y reproduce las voces de Atlas y Asti.

Ejecutar desde C:\\NOVA:
  python scripts/demo_voice.py             solo la voz local (Piper)
  python scripts/demo_voice.py --online    prueba la voz en línea y, si
                                           falla, vuelve a la local
"""

import sys
import time

from nova.core import Identity
from nova.core.logging_setup import setup_logging
from nova.storage.paths import default_logs_dir, default_voices_dir
from nova.voice import (
    EdgeTTSProvider,
    PiperTTSProvider,
    SoundDevicePlayer,
    TTSRouter,
)

PHRASE = "Buenos días, Jefe. Todos los sistemas funcionan con normalidad."


def main() -> None:
    prefer_online = "--online" in sys.argv

    setup_logging(default_logs_dir(), debug=True)

    router = TTSRouter(
        local=PiperTTSProvider(default_voices_dir()),
        online=EdgeTTSProvider(),
        prefer_online=prefer_online,
    )
    player = SoundDevicePlayer()

    for identity in (Identity.ATLAS, Identity.ASTI):
        start = time.perf_counter()
        result = router.synthesize(PHRASE, identity)
        elapsed = time.perf_counter() - start

        if not result.success:
            print(f"[{identity.value}] ERROR {result.error.code}: "
                  f"{result.error.message}")
            continue

        audio = result.value

        print(
            f"[{identity.value}] voz '{audio.provider}': síntesis "
            f"{elapsed:.2f}s, audio {audio.duration_seconds:.1f}s"
        )

        played = player.play(audio)

        if not played.success:
            print(f"[{identity.value}] ERROR {played.error.code}")


if __name__ == "__main__":
    main()