from nova.core import Identity
from nova.personality import parse_identity_command

COMMANDS = {
    "cambia a Asti": Identity.ASTI,
    "Cambia a Atlas.": Identity.ATLAS,
    "pasa a Abi": Identity.ASTI,
    "activa a asti": Identity.ASTI,
    "Cámbiate a Atlas": Identity.ATLAS,
    "quiero hablar con Atlas": Identity.ATLAS,
    "habla como Asti": Identity.ASTI,
    "háblame como Atlas": Identity.ATLAS,
    "por favor, cambia a Abi": Identity.ASTI,
    "cambia a Atlas por favor": Identity.ATLAS,
    "  CAMBIA A ASTI  ": Identity.ASTI,
    "habla con Abi": Identity.ASTI,
}

NOT_COMMANDS = [
    "háblame de Atlas el titán",
    "cambia el fondo",
    "Asti es un nombre bonito",
    "cambia a Atlas de lugar el sofá",
    "pasa a Atlas la sal",
    "hola",
    "",
    "atlas",
    "cuéntame sobre Abi",
    "quiero hablar con Atlas sobre mi proyecto",
    "cambia a asti y dime la hora",
]


def test_identity_commands_are_recognized():
    for text, expected in COMMANDS.items():
        assert parse_identity_command(text) == expected, text


def test_ordinary_sentences_are_not_commands():
    for text in NOT_COMMANDS:
        assert parse_identity_command(text) is None, text


def test_abi_is_an_alias_of_asti():
    assert parse_identity_command("pasa a Abi") == Identity.ASTI