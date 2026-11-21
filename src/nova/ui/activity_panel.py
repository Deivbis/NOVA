"""Lógica de la actividad del Dashboard (Fase 10.4), sin Qt."""

from nova.activity import ActivityService
from nova.ui.time_format import friendly_time

_GROUPS = {
    "memory": ("memory", "Memoria"),
    "learning": ("sparkle", "Aprendizaje"),
    "task": ("clock", "Tareas"),
    "automation": ("cpu", "Automatización"),
    "routine": ("doc", "Rutinas"),
    "plugin": ("gear", "Plugins"),
    "permission": ("gear", "Permisos"),
    "project": ("folder", "Proyectos"),
}

_WHAT = {
    "memory.created": "Recuerdo guardado",
    "memory.updated": "Recuerdo actualizado",
    "memory.deactivated": "Recuerdo olvidado",
    "memory.reactivated": "Recuerdo reactivado",
    "memory.purged": "Recuerdo borrado definitivamente",
    "learning.proposed": "Propuesta de aprendizaje",
    "learning.confirmed": "Aprendizaje confirmado",
    "learning.rejected": "Aprendizaje rechazado",
    "task.created": "Pendiente o recordatorio creado",
    "task.done": "Pendiente completado",
    "task.cancelled": "Pendiente cancelado",
    "task.fired": "Recordatorio disparado",
    "automation.executed": "Acción ejecutada",
    "automation.confirmed": "Acción confirmada",
    "automation.denied": "Acción denegada",
    "automation.cancelled": "Acción cancelada",
    "routine.saved": "Rutina guardada",
    "routine.removed": "Rutina eliminada",
    "routine.executed": "Rutina ejecutada",
    "plugin.enabled": "Plugin activado",
    "plugin.disabled": "Plugin desactivado",
    "plugin.failed": "Un plugin falló",
    "plugin.denied": "Permiso de plugin denegado",
    "permission.granted": "Permiso concedido",
    "permission.revoked": "Permiso revocado",
    "project.created": "Proyecto creado",
    "project.updated": "Proyecto actualizado",
    "project.deleted": "Proyecto eliminado",
}


def describe(action: str) -> tuple[str, str, str]:
    icon, who = _GROUPS.get(action.split(".", 1)[0], ("doc", "Sistema"))

    return icon, who, _WHAT.get(action, "Actividad registrada")


class ActivityPanel:
    def __init__(self, service: ActivityService) -> None:
        self._service = service

    def recent(self, days: int) -> dict:
        result = self._service.recent(days)

        if not result.success:
            return {"total": 0, "items": []}

        items = []

        for event in result.value.events:
            icon, who, what = describe(event.action)
            items.append(
                {
                    "ic": icon,
                    "who": who,
                    "what": what,
                    "when": friendly_time(event.created_at),
                }
            )

        return {"total": result.value.total, "items": items}