from nova.core.commands import Command


def test_command_has_name():
    command = Command(name="test.command")

    assert command.name == "test.command"


def test_command_has_unique_id():
    first = Command(name="test.command")
    second = Command(name="test.command")

    assert first.command_id != second.command_id


def test_command_can_require_internet():
    command = Command(
        name="web.search",
        requires_internet=True,
    )

    assert command.requires_internet is True