"""Métricas reales del equipo para el Dashboard (psutil)."""

import os
import time

from PySide6.QtCore import Property, QObject, QTimer, Signal

try:
    import psutil
except ImportError:
    psutil = None

HISTORY = 30


def _fmt_uptime(seconds: float) -> str:
    minutes = int(seconds // 60)
    days, minutes = divmod(minutes, 1440)
    hours, minutes = divmod(minutes, 60)

    if days:
        return f"{days} d {hours} h"

    return f"{hours} h {minutes} min" if hours else f"{minutes} min"


class SystemMetrics(QObject):
    changed = Signal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._cur = {"cpu": 0.0, "ram": 0.0, "disk": 0.0, "net": 0.0}
        self._hist: dict[str, list[float]] = {k: [] for k in self._cur}
        self._info = {"uptime": "-", "procs": "-", "cores": "-", "ram": "-"}
        self._primed = False
        self._last_net = psutil.net_io_counters() if psutil else None

        if psutil:
            psutil.cpu_percent()

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(2000)
        self._tick()

    def _tick(self) -> None:
        if psutil is None:
            return

        memory = psutil.virtual_memory()
        now = psutil.net_io_counters()
        moved = (now.bytes_recv + now.bytes_sent) - (
            self._last_net.bytes_recv + self._last_net.bytes_sent
        )
        self._last_net = now
        values = {
            "cpu": psutil.cpu_percent(),
            "ram": memory.percent,
            "disk": psutil.disk_usage(os.path.abspath(os.sep)).percent,
            "net": min(100.0, moved / 2 / (1024 * 1024) * 100),
        }
        self._info = {
            "uptime": _fmt_uptime(time.time() - psutil.boot_time()),
            "procs": str(len(psutil.pids())),
            "cores": str(psutil.cpu_count(logical=True)),
            "ram": f"{memory.total / 1024 ** 3:.0f} GB",
        }

        for key, value in values.items():
            self._cur[key] = value
            history = self._hist[key]
            self._hist[key] = (
                [value] * HISTORY
                if not self._primed
                else (history + [value])[-HISTORY:]
            )

        self._primed = True
        self.changed.emit()

    cpu = Property(float, lambda s: s._cur["cpu"], notify=changed)
    ram = Property(float, lambda s: s._cur["ram"], notify=changed)
    disk = Property(float, lambda s: s._cur["disk"], notify=changed)
    net = Property(float, lambda s: s._cur["net"], notify=changed)
    cpuHistory = Property("QVariantList", lambda s: s._hist["cpu"], notify=changed)
    ramHistory = Property("QVariantList", lambda s: s._hist["ram"], notify=changed)
    diskHistory = Property("QVariantList", lambda s: s._hist["disk"], notify=changed)
    netHistory = Property("QVariantList", lambda s: s._hist["net"], notify=changed)
    sysUptime = Property(str, lambda s: s._info["uptime"], notify=changed)
    sysProcs = Property(str, lambda s: s._info["procs"], notify=changed)
    sysCores = Property(str, lambda s: s._info["cores"], notify=changed)
    sysRam = Property(str, lambda s: s._info["ram"], notify=changed)