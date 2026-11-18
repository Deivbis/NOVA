from datetime import datetime

from nova.plugin_sdk.sdk import PluginBase

_DAYS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
_MONTHS = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
    "agosto", "septiembre", "octubre", "noviembre", "diciembre",
]


class Plugin(PluginBase):
    def on_command(self, command, text, groups):
        now = datetime.now()

        if command == "hora":
            return f"Son las {now:%H:%M}, Jefe."

        return (
            f"Hoy es {_DAYS[now.weekday()]} {now.day} de "
            f"{_MONTHS[now.month - 1]} de {now.year}, Jefe."
        )