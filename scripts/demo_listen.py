"""Demo de escucha (v0.3): micrófono -> fin de frase automático -> texto.

Ejecutar desde C:\\NOVA:  python scripts/demo_listen.py
Habla con normalidad; la grabación se detiene sola cuando callas.
"""

import threading
import time

from nova.voice import (
    FasterWhisperSTT,
    MicrophoneRecorder,
    load_voice_settings,
)


def main() -> None:
    settings = load_voice_settings()
    recorder = MicrophoneRecorder()
    stt = FasterWhisperSTT(vocabulary=settings.vocabulary)

    print(f"Vocabulario: {', '.join(settings.vocabulary)}")
    input("Pulsa Enter y habla (se detiene sola cuando calles)... ")

    recorded = recorder.record(threading.Event())

    if not recorded.success:
        print(f"ERROR {recorded.error.code}: {recorded.error.message}")
        return

    recording = recorded.value

    print(
        f"Fin: {recording.reason} | duración {recording.seconds:.1f}s | "
        f"pico {recording.peak_rms:.3f} | "
        f"ruido de fondo {recording.noise_floor:.4f}"
    )

    if recording.audio is None:
        print("No se detectó voz. Si hablaste, pásame estas cifras.")
        return

    start = time.perf_counter()
    result = stt.transcribe(recording.audio)
    elapsed = time.perf_counter() - start

    print(f"Transcripción en {elapsed:.1f}s (la primera vez incluye la carga):")

    if result.success:
        print(result.value)
    else:
        print(f"ERROR {result.error.code}: {result.error.message}")

    stt.shutdown()


if __name__ == "__main__":
    main()