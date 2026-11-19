"""Formatos de fecha para la interfaz (hora local)."""

from datetime import datetime

_WEEKDAYS = ("Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom")


def friendly_time(moment: datetime) -> str:
    local = moment.astimezone()
    days = (datetime.now().astimezone().date() - local.date()).days

    if days <= 0:
        return local.strftime("%H:%M")

    if days == 1:
        return "Ayer"

    if days < 7:
        return _WEEKDAYS[local.weekday()]

    return local.strftime("%d/%m")


def full_time(moment: datetime) -> str:
    return moment.astimezone().strftime("%d/%m/%Y %H:%M")
