"""Logging central de NOVA (NOVA-SPEC-014 §9, DOC-018, DOC-022).

Regla de privacidad: nunca registrar contenido de conversaciones,
payloads de comandos, secretos ni datos personales.
"""

from __future__ import annotations

import json
import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

ROOT_LOGGER_NAME = "nova"
LOG_FILE_NAME = "nova.log"
_HANDLER_MARK = "_nova_handler"


class JsonLineFormatter(logging.Formatter):
    """Formatea cada registro como una línea JSON."""

    def format(self, record: logging.LogRecord) -> str:
        data = {
            "time": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        if record.exc_info:
            data["exception"] = self.formatException(record.exc_info)

        return json.dumps(data, ensure_ascii=False)


def get_logger(name: str) -> logging.Logger:
    """Devuelve un logger dentro de la jerarquía 'nova'."""
    if name == ROOT_LOGGER_NAME or name.startswith(ROOT_LOGGER_NAME + "."):
        return logging.getLogger(name)

    return logging.getLogger(f"{ROOT_LOGGER_NAME}.{name}")


def setup_logging(log_dir: Path, debug: bool = False) -> logging.Logger:
    """Configura el logging de NOVA. Es seguro llamarla varias veces."""
    shutdown_logging()

    log_dir.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger(ROOT_LOGGER_NAME)
    logger.setLevel(logging.DEBUG if debug else logging.INFO)

    file_handler = RotatingFileHandler(
        log_dir / LOG_FILE_NAME,
        maxBytes=1_000_000,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setFormatter(JsonLineFormatter())
    setattr(file_handler, _HANDLER_MARK, True)
    logger.addHandler(file_handler)

    # Un .exe sin consola puede tener sys.stderr = None.
    if sys.stderr is not None:
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
            )
        )
        setattr(console_handler, _HANDLER_MARK, True)
        logger.addHandler(console_handler)

    return logger


def shutdown_logging() -> None:
    """Quita y cierra los handlers que instaló setup_logging."""
    logger = logging.getLogger(ROOT_LOGGER_NAME)

    for handler in list(logger.handlers):
        if getattr(handler, _HANDLER_MARK, False):
            logger.removeHandler(handler)
            handler.close()