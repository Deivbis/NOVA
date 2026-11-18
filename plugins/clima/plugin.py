import json
from urllib.parse import quote

from nova.plugin_sdk.sdk import PluginBase, PluginError

_GEO = (
    "https://geocoding-api.open-meteo.com/v1/search"
    "?count=1&language=es&format=json&name="
)
_FORECAST = (
    "https://api.open-meteo.com/v1/forecast?timezone=auto"
    "&current=temperature_2m,apparent_temperature,weather_code,wind_speed_10m"
    "&latitude={lat}&longitude={lon}"
)


def _sky(code: int) -> str:
    if code == 0:
        return "despejado"
    if code in (1, 2):
        return "parcialmente nublado"
    if code == 3:
        return "nublado"
    if code in (45, 48):
        return "con niebla"
    if 51 <= code <= 57:
        return "con llovizna"
    if 61 <= code <= 67 or 80 <= code <= 82:
        return "con lluvia"
    if 71 <= code <= 77 or code in (85, 86):
        return "con nieve"
    if code >= 95:
        return "con tormenta"
    return "variable"


class Plugin(PluginBase):
    def on_command(self, command, text, groups):
        city = groups.get("ciudad", "").strip()[:60]

        if not city:
            return "¿De qué ciudad, Jefe?"

        try:
            places = json.loads(self.ctx.http_get(_GEO + quote(city))).get("results")

            if not places:
                return f"No encontré la ciudad «{city}», Jefe."

            place = places[0]
            data = json.loads(self.ctx.http_get(
                _FORECAST.format(lat=place["latitude"], lon=place["longitude"])
            ))
            now = data["current"]
            return (
                f"En {place.get('name', city)} hacen "
                f"{now['temperature_2m']:.0f} grados (sensación de "
                f"{now['apparent_temperature']:.0f}), "
                f"{_sky(int(now['weather_code']))}, con viento de "
                f"{now['wind_speed_10m']:.0f} km/h."
            )
        except (PluginError, ValueError, KeyError, TypeError):
            return "No pude consultar el clima ahora, Jefe."