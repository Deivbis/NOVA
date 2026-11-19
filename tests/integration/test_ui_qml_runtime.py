import os
import subprocess
import sys
from pathlib import Path


def test_qml_runtime_loads_windows_and_navigation():
    project_root = Path(__file__).resolve().parents[2]
    probe = Path(__file__).with_name("_qml_runtime_probe.py")

    env = os.environ.copy()
    env["QT_QPA_PLATFORM"] = "offscreen"
    env["QT_QUICK_BACKEND"] = "software"

    result = subprocess.run(
        [sys.executable, str(probe)],
        cwd=project_root,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )

    output = result.stdout + "\n" + result.stderr

    assert result.returncode == 0, output
    assert "QML_RUNTIME_OK" in result.stdout
    assert "Ventanas cargadas: 2" in result.stdout
    assert "Título: NOVA" in result.stdout
    assert "Página recibida por el bridge: 4" in result.stdout
