from nova.core import (
    Capability,
    CapabilityManager,
    ConnectivityState,
    CoreOrchestrator,
    RiskLevel,
)


def local_capability(capability_id="chat.local"):
    return Capability(
        id=capability_id,
        name="Chat local",
        description="Conversación con el modelo local.",
    )


def internet_capability():
    return Capability(
        id="weather.query",
        name="Clima",
        description="Consulta del clima.",
        requires_internet=True,
    )


def test_capability_defaults():
    capability = local_capability()

    assert capability.provider is None
    assert capability.requires_internet is False
    assert capability.risk_level == RiskLevel.LOW


def test_register_and_get_capability():
    manager = CapabilityManager()
    capability = local_capability()

    assert manager.register(capability).success
    assert manager.get("chat.local") == capability


def test_duplicate_registration_fails():
    manager = CapabilityManager()
    manager.register(local_capability())

    result = manager.register(local_capability())

    assert not result.success
    assert result.error.code == "CAPABILITY_ALREADY_REGISTERED"


def test_list_capabilities_is_sorted_by_id():
    manager = CapabilityManager()
    manager.register(local_capability("b.second"))
    manager.register(local_capability("a.first"))

    ids = [item.id for item in manager.list_capabilities()]

    assert ids == ["a.first", "b.second"]


def test_unknown_capability_is_unavailable():
    availability = CapabilityManager().availability(
        "no.existe",
        ConnectivityState.ONLINE,
    )

    assert not availability.available
    assert availability.code == "CAPABILITY_NOT_FOUND"


def test_local_capability_is_available_without_internet():
    manager = CapabilityManager()
    manager.register(local_capability())

    for connectivity in ConnectivityState:
        assert manager.availability("chat.local", connectivity).available


def test_disabled_capability_is_unavailable_until_enabled():
    manager = CapabilityManager()
    manager.register(local_capability())

    manager.set_enabled("chat.local", False)
    disabled = manager.availability("chat.local", ConnectivityState.ONLINE)

    manager.set_enabled("chat.local", True)
    enabled = manager.availability("chat.local", ConnectivityState.ONLINE)

    assert not disabled.available
    assert disabled.code == "CAPABILITY_DISABLED"
    assert enabled.available


def test_set_enabled_unknown_capability_fails():
    result = CapabilityManager().set_enabled("no.existe", False)

    assert not result.success
    assert result.error.code == "CAPABILITY_NOT_FOUND"


def test_internet_capability_requires_online_connectivity():
    manager = CapabilityManager()
    manager.register(internet_capability())

    for connectivity in (
        ConnectivityState.OFFLINE,
        ConnectivityState.UNKNOWN,
    ):
        availability = manager.availability("weather.query", connectivity)

        assert not availability.available
        assert availability.code == "INTERNET_REQUIRED"

    assert manager.availability(
        "weather.query",
        ConnectivityState.ONLINE,
    ).available


def test_orchestrator_exposes_capability_manager():
    core = CoreOrchestrator()

    assert isinstance(core.capabilities, CapabilityManager)


def test_orchestrator_availability_follows_connectivity():
    core = CoreOrchestrator()
    core.capabilities.register(internet_capability())

    assert not core.capability_availability("weather.query").available

    core.set_connectivity(ConnectivityState.ONLINE)

    assert core.capability_availability("weather.query").available