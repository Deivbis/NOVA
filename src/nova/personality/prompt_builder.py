from nova.core.identity import Identity
from nova.personality.profiles import profile_for


def build_messages(
    identity: Identity,
    history: list[dict[str, str]],
) -> list[dict[str, str]]:
    """Antepone el prompt de la identidad al historial (sin modificarlo)."""
    system = {
        "role": "system",
        "content": profile_for(identity).system_prompt,
    }

    return [system, *history]