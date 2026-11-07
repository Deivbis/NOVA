import json
import logging
from logging.handlers import RotatingFileHandler

import pytest

from nova.core.logging_setup import (
    LOG_FILE_NAME,
    ROOT_LOGGER_NAME,
    get_logger,
    setup_logging,
    shutdown_logging,
)


@pytest.fixture(autouse=True)
def clean_logging():
    shutdown_logging()
    yield
    shutdown_logging()


def read_records(log_dir):
    lines = (log_dir / LOG_FILE_NAME).read_text(
        encoding="utf-8"
    ).splitlines()

    return [json.loads(line) for line in lines]


def test_setup_creates_log_file_with_json_lines(tmp_path):
    log_dir = tmp_path / "logs"

    setup_logging(log_dir)
    get_logger("nova.test").info("Hola NOVA")

    record = read_records(log_dir)[-1]

    assert record["message"] == "Hola NOVA"
    assert record["level"] == "INFO"
    assert record["logger"] == "nova.test"


def test_setup_is_idempotent(tmp_path):
    log_dir = tmp_path / "logs"

    setup_logging(log_dir)
    setup_logging(log_dir)

    handlers = logging.getLogger(ROOT_LOGGER_NAME).handlers
    file_handlers = [
        handler
        for handler in handlers
        if isinstance(handler, RotatingFileHandler)
    ]

    assert len(file_handlers) == 1


def test_debug_flag_controls_level(tmp_path):
    log_dir = tmp_path / "logs"

    assert setup_logging(log_dir, debug=True).level == logging.DEBUG
    assert setup_logging(log_dir, debug=False).level == logging.INFO


def test_exceptions_are_logged_with_traceback(tmp_path):
    log_dir = tmp_path / "logs"

    setup_logging(log_dir)
    logger = get_logger("nova.test")

    try:
        raise ValueError("fallo de prueba")
    except ValueError:
        logger.exception("Algo falló")

    record = read_records(log_dir)[-1]

    assert "ValueError" in record["exception"]


def test_get_logger_uses_nova_hierarchy():
    assert get_logger("storage").name == "nova.storage"
    assert get_logger("nova.core").name == "nova.core"