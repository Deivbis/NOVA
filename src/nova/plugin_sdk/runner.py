"""Proceso de un plugin. Protocolo: una línea JSON por mensaje.

host → plugin: {"type":"command","id":N,"command":..,"text":..,"groups":{..}}
               {"type":"result","id":M,"ok":bool,"value"|"error":..}
               {"type":"stop"}
plugin → host: {"type":"ready"} | {"type":"reply","id":N,"text":..}
               {"type":"error","id":N,"error":..}
               {"type":"call","id":M,"method":..,"params":{..}}
"""

import importlib.util
import json
import sys
from pathlib import Path

from nova.plugin_sdk.sdk import Context, PluginError


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        return 2

    folder = Path(argv[1]).resolve()
    inbound, outbound = sys.stdin, sys.stdout
    sys.stdout = sys.stderr  # un print() del plugin no rompe el protocolo
    counter = {"n": 0}

    def send(message: dict) -> None:
        outbound.write(json.dumps(message) + "\n")
        outbound.flush()

    def call(method: str, **params):
        counter["n"] += 1
        call_id = counter["n"]
        send({"type": "call", "id": call_id, "method": method, "params": params})

        for line in inbound:
            try:
                message = json.loads(line)
            except ValueError:
                continue

            if message.get("type") == "stop":
                raise SystemExit(0)

            if message.get("type") == "result" and message.get("id") == call_id:
                if message.get("ok"):
                    return message.get("value")

                raise PluginError(str(message.get("error", "Error.")))

        raise SystemExit(0)

    try:
        sys.path.insert(0, str(folder))
        spec = importlib.util.spec_from_file_location(
            "nova_plugin", folder / "plugin.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        plugin = module.Plugin(Context(call))
    except Exception as exc:
        send({"type": "error", "id": 0, "error": type(exc).__name__})
        return 1

    send({"type": "ready"})

    for line in inbound:
        try:
            message = json.loads(line)
        except ValueError:
            continue

        kind = message.get("type")

        if kind == "stop":
            break

        if kind != "command":
            continue

        try:
            reply = plugin.on_command(
                str(message.get("command", "")),
                str(message.get("text", "")),
                dict(message.get("groups", {})),
            )
            send({
                "type": "reply",
                "id": message.get("id"),
                "text": "" if reply is None else str(reply),
            })
        except SystemExit:
            raise
        except Exception as exc:
            send({
                "type": "error",
                "id": message.get("id"),
                "error": type(exc).__name__,
            })

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))