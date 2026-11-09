import logging

from nova.core import Command, CoreOrchestrator, Result


def test_unknown_command_is_logged_as_warning(caplog):
    core = CoreOrchestrator()

    with caplog.at_level(logging.WARNING, logger="nova"):
        result = core.dispatch(Command(name="no.existe"))

    assert not result.success
    assert any("no.existe" in r.message for r in caplog.records)


def test_handler_exception_is_logged_with_traceback(caplog):
    core = CoreOrchestrator()

    def broken(command):
        raise RuntimeError("boom")

    core.register_command("test.broken", broken)

    with caplog.at_level(logging.ERROR, logger="nova"):
        result = core.dispatch(Command(name="test.broken"))

    assert result.error.code == "COMMAND_EXECUTION_ERROR"
    assert any(r.exc_info for r in caplog.records)


def test_payload_is_never_logged(caplog):
    core = CoreOrchestrator()
    core.register_command("test.echo", lambda c: Result.ok("ok"))

    with caplog.at_level(logging.DEBUG, logger="nova"):
        core.dispatch(
            Command(
                name="test.echo",
                payload={"message": "dato-privado-123"},
            )
        )

    assert "dato-privado-123" not in caplog.text