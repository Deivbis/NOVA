import sys

from nova.runtime import PLUGIN_RUNNER_FLAG


def run() -> int:
    if len(sys.argv) == 3 and sys.argv[1] == PLUGIN_RUNNER_FLAG:
        from nova.plugin_sdk.runner import main as runner_main

        return runner_main([sys.argv[0], sys.argv[2]])

    from nova.ui.qml.application import main

    return main()


if __name__ == "__main__":
    raise SystemExit(run())