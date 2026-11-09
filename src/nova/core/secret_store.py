"""Acceso a secretos mediante variables de entorno (SPEC-014 §5, DOC-022).

Los secretos nunca se guardan en Git, en la base de datos ni en el log.
Convención: el secreto 'gemini_api_key' se lee de NOVA_GEMINI_API_KEY.
"""

import os
from collections.abc import Mapping

from nova.core.result import Result

ENV_PREFIX = "NOVA_"


def secret_env_name(name: str) -> str:
    """Nombre de la variable de entorno que guarda el secreto."""
    return ENV_PREFIX + name.strip().upper().replace("-", "_")


def get_secret(
    name: str,
    environ: Mapping[str, str] | None = None,
) -> str | None:
    """Devuelve el secreto o None si falta o está vacío."""
    env = os.environ if environ is None else environ
    value = env.get(secret_env_name(name), "").strip()

    return value or None


def require_secret(
    name: str,
    environ: Mapping[str, str] | None = None,
) -> Result[str]:
    """Devuelve el secreto o un error estructurado si falta."""
    value = get_secret(name, environ)

    if value is None:
        return Result.fail(
            code="SECRET_NOT_FOUND",
            message=(
                f"Falta la variable de entorno {secret_env_name(name)}."
            ),
        )

    return Result.ok(value)