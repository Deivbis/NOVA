from nova.core import ConnectivityState, CoreOrchestrator, NovaState
from nova.core.logging_setup import shutdown_logging
from nova.main import create_configuration, create_core, main


def test_main_exists():
    assert callable(main)


def test_create_core_returns_orchestrator():
    core = create_core()

    assert isinstance(core, CoreOrchestrator)


def test_core_starts_idle():
    core = create_core()

    assert core.state == NovaState.IDLE


def test_core_starts_with_unknown_connectivity():
    core = create_core()

    assert core.connectivity == ConnectivityState.UNKNOWN



def test_create_core_registers_system_service():
    core = create_core()

    assert core.capability_availability("system").available


def test_configuration_loads_from_any_working_directory(
    tmp_path,
    monkeypatch,
):
    monkeypatch.chdir(tmp_path)

    config = create_configuration().initialize()

    assert config.nova.name == "NOVA"


def test_main_runs_end_to_end_with_isolated_data_dir(
    tmp_path,
    monkeypatch,
    capsys,
):
    monkeypatch.setenv("NOVA_DATA_DIR", str(tmp_path))

    try:
        main()
    finally:
        shutdown_logging()

    output = capsys.readouterr().out

    assert "Estado: idle" in output
    assert "Almacenamiento: SQLite operativo" in output
    assert (tmp_path / "nova.db").exists()
    assert (tmp_path / "logs" / "nova.log").exists()