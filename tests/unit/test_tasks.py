from datetime import datetime, timedelta, timezone

from nova.storage import StorageService
from nova.tasks import TaskCommandHandler, TaskService
from nova.tasks.timeparse import parse_when

TZ = timezone(timedelta(hours=-5))
NOW = datetime(2026, 11, 17, 14, 0, tzinfo=TZ)


def test_parse_relative_and_absolute():
    title, due, error = parse_when("llamar a mamá en 10 minutos", NOW)
    assert (title, due, error) == ("llamar a mamá", NOW + timedelta(minutes=10), None)

    _, due, _ = parse_when("a las 5 pm llamar a mamá", NOW)
    assert due == NOW.replace(hour=17, minute=0)

    _, due, _ = parse_when("a las 5 llamar a mamá", NOW)
    assert due == NOW.replace(hour=17, minute=0)

    title, due, _ = parse_when("mañana a las 9 enviar informe", NOW)
    assert due == NOW.replace(day=18, hour=9, minute=0)
    assert title == "enviar informe"

    _, due, _ = parse_when("mañana enviar informe", NOW)
    assert due == NOW.replace(day=18, hour=9, minute=0)

    _, due, _ = parse_when("a las 8 de la mañana x", NOW)
    assert due == NOW.replace(day=18, hour=8, minute=0)


def test_parse_none_and_errors():
    assert parse_when("enviar informe", NOW)[1] is None
    assert parse_when("a las 25 x", NOW)[2] is not None
    assert parse_when("hoy x", NOW)[2] is not None


def make(tmp_path):
    storage = StorageService(tmp_path / "t.db")
    storage.initialize()
    clock = {"now": NOW}
    service = TaskService(storage.task_repository, lambda: clock["now"])

    return storage, clock, TaskCommandHandler(service)


def test_reminder_fires_once_and_late_wording(tmp_path):
    storage, clock, handler = make(tmp_path)

    assert "hoy a las 14:10" in handler.reply_to(
        "recuérdame llamar a mamá en 10 minutos"
    )
    assert handler.due_messages() is None

    clock["now"] = NOW + timedelta(minutes=11)
    assert "recordatorio: llamar a mamá" in handler.due_messages()
    assert handler.due_messages() is None

    handler.reply_to("recuérdame pagar luz en 5 minutos")
    clock["now"] = NOW + timedelta(hours=3)
    assert "tenías un recordatorio" in handler.due_messages()
    storage.close()


def test_todos_list_complete_cancel(tmp_path):
    storage, _, handler = make(tmp_path)

    handler.reply_to("anota comprar pan")
    handler.reply_to("recuérdame enviar informe mañana a las 9")
    listing = handler.reply_to("qué tengo pendiente")

    assert listing.splitlines()[1].startswith("1. enviar informe")
    assert "2. comprar pan" in listing

    assert "completado" in handler.reply_to("completa el 2")
    assert "Cancelado" in handler.reply_to("cancela el recordatorio informe")
    assert "No tienes pendientes" in handler.reply_to("mis pendientes")
    storage.close()


def test_missing_time_is_asked(tmp_path):
    storage, _, handler = make(tmp_path)

    assert "¿Cuándo" in handler.reply_to("recuérdame llamar a mamá")
    assert handler.reply_to("hola") is None
    storage.close()