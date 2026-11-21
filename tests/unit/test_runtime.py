from nova import runtime


def test_dev_paths():
    assert not runtime.is_frozen()
    assert (runtime.app_root() / "config" / "default.toml").is_file()
    assert runtime.plugins_dir().is_dir()


def test_plugin_command(monkeypatch, tmp_path):
    assert runtime.plugin_runner_command(tmp_path)[1:3] == [
        "-m", "nova.plugin_sdk.runner",
    ]

    monkeypatch.setattr(runtime, "is_frozen", lambda: True)

    assert runtime.plugin_runner_command(tmp_path)[1] == runtime.PLUGIN_RUNNER_FLAG