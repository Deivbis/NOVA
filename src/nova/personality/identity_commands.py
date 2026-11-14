"""Reconoce las órdenes de cambio de identidad (SPEC-002).

Solo coincide con la frase completa ("cambia a Asti", "pasa a Abi"...), para
no confundir "háblame de Atlas el titán" con una orden. "Abi" es el apodo
de Asti.
"""

import re

from nova.core.identity import Identity

_ALIASES = {
    "atlas": Identity.ATLAS,
    "asti": Identity.ASTI,
    "abi": Identity.ASTI,
}

_COMMAND = re.compile(
    r"^\s*(?:por favor[ ,]*)?"
    r"(?:cambia(?:te)?|c[aá]mbiate|pasa|activa|ponme|quiero hablar|hablar|"
    r"habla|hablame|h[aá]blame)"
    r"(?:\s+(?:a|con|como|de))?\s+"
    r"(?:con\s+)?(atlas|asti|abi)"
    r"(?:[ ,]*(?:por favor|ahora))?\s*[.!?¡]*\s*$",
    re.IGNORECASE,
)


def parse_identity_command(text: str) -> Identity | None:
    match = _COMMAND.match(text.strip())

    return _ALIASES[match.group(1).lower()] if match else None