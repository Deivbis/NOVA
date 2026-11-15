from collections.abc import Sequence

from nova.core.identity import Identity
from nova.personality.profiles import profile_for

MEMORY_HEADER = (
    "Recuerdos autorizados del usuario "
    "(úsalos solo si vienen al caso; no los menciones si no):"
)


def build_messages(
    identity: Identity,
    history: list[dict[str, str]],
    memories: Sequence[str] = (),
) -> list[dict[str, str]]:
    """Antepone el prompt de la identidad (y los recuerdos que vengan al caso).

    Los recuerdos van al final del prompt de sistema para no romper el
    prefijo estable que Ollama reutiliza en caché.
    """
    content = profile_for(identity).system_prompt

    if memories:
        lines = "\n".join(f"- {item}" for item in memories)
        content = f"{content}\n{MEMORY_HEADER}\n{lines}"

    return [{"role": "system", "content": content}, *history]