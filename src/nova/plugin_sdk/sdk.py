"""API que ve un plugin. Se importa con: from nova.plugin_sdk.sdk import ..."""


class PluginError(Exception):
    """Llamada a la API de NOVA rechazada o fallida."""


class Context:
    """Capacidades que NOVA presta al plugin (cada una exige un permiso)."""

    def __init__(self, call) -> None:
        self._call = call

    def speak(self, text: str) -> None:  # permiso: speak
        self._call("speak", text=text)

    def http_get(self, url: str) -> str:  # permiso: network (+ dominios)
        return self._call("http_get", url=url)

    def memory_search(self, query: str) -> list[str]:  # permiso: memory.read
        return self._call("memory_search", query=query)

    def open_target(self, kind: str, text: str) -> None:  # automation.open
        self._call("open_target", kind=kind, text=text)

    def media(self, command: str) -> None:  # automation.media
        self._call("media", command=command)


class PluginBase:
    def __init__(self, ctx: Context) -> None:
        self.ctx = ctx

    def on_command(self, command: str, text: str, groups: dict) -> str | None:
        return None