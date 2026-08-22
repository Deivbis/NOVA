from nova.core import (
    Command,
    ConnectivityState,
    CoreOrchestrator,
    Result,
)


def test_unknown_command_returns_failure():
    core = CoreOrchestrator()

    result = core.dispatch(
        Command(name="unknown.command")
    )

    assert result.success is False
    assert result.error is not None
    assert result.error.code == "COMMAND_NOT_FOUND"


def test_offline_command_requiring_internet_is_rejected():
    core = CoreOrchestrator()

    core.set_connectivity(
        ConnectivityState.OFFLINE
    )

    result = core.dispatch(
        Command(
            name="web.search",
            requires_internet=True,
        )
    )

    assert result.success is False
    assert result.error is not None
    assert result.error.code == "INTERNET_REQUIRED"


def test_registered_command_is_executed():
    core = CoreOrchestrator()

    def handler(command: Command):
        return Result.ok("ejecutado")

    core.register_command(
        "test.command",
        handler,
    )

    result = core.dispatch(
        Command(name="test.command")
    )

    assert result.success is True
    assert result.value == "ejecutado"