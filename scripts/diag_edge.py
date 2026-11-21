"""Diagnóstico de la voz en línea (Edge). Uso: python scripts\\diag_edge.py"""

import asyncio
import sys
from importlib.metadata import version
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

TEXT = "Hola Jefe, esta es una prueba de la voz en línea."


async def fetch() -> bytes:
    import edge_tts

    data = bytearray()

    async for chunk in edge_tts.Communicate(TEXT, "es-MX-JorgeNeural").stream():
        if chunk["type"] == "audio":
            data.extend(chunk["data"])

    return bytes(data)


print("edge-tts", version("edge-tts"), "| av", version("av"))

try:
    mp3 = asyncio.run(asyncio.wait_for(fetch(), 15))
    print(f"1) Descarga OK ({len(mp3)} bytes)")
except Exception as exc:
    print(f"1) FALLA la descarga: {type(exc).__name__}: {exc}")
    sys.exit(1)

try:
    from nova.voice.edge_tts_provider import _decode_mp3

    pcm, rate = _decode_mp3(mp3)
    print(f"2) Decodificación OK ({len(pcm)} bytes a {rate} Hz)")
except Exception as exc:
    print(f"2) FALLA la decodificación: {type(exc).__name__}: {exc}")
    sys.exit(1)

print("Todo bien: en NOVA activa «Voz en línea» en Configuración.")