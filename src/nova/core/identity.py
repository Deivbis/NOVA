from enum import Enum


class Identity(str, Enum):
    """Identidades de NOVA (NOVA-SPEC-002, D-017).

    Atlas es la identidad masculina y Asti la femenina. Cambiar de
    identidad no afecta a la conversación ni a la memoria.
    """

    ATLAS = "atlas"
    ASTI = "asti"