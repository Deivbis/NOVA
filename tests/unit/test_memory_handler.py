from nova.memory import (
    MemoryAction as A,
    MemoryCommand as C,
    MemoryCommandHandler,
    MemoryService,
)
from nova.storage import StorageService


def create_handler(tmp_path):
    storage = StorageService(tmp_path / "nova.db")
    storage.initialize()
    service = MemoryService(storage.memory_repository)

    return MemoryCommandHandler(service), service, storage


def test_remember_saves_and_confirms(tmp_path):
    handler, service, storage = create_handler(tmp_path)

    reply = handler.handle(C(A.REMEMBER, "me gusta el rock", "Música"))

    assert reply == "Anotado, Jefe, en «Música»: me gusta el rock"
    assert len(service.list_memories().value) == 1

    storage.close()


def test_remembering_the_same_thing_twice_says_so(tmp_path):
    handler, _, storage = create_handler(tmp_path)

    handler.handle(C(A.REMEMBER, "me llamo Deivbis"))
    reply = handler.handle(C(A.REMEMBER, "me llamo Deivbis"))

    assert reply == "Ya lo tenía anotado, Jefe."

    storage.close()


def test_forget_by_topic_deactivates_a_single_match(tmp_path):
    handler, service, storage = create_handler(tmp_path)
    service.remember("mi hermano se llama Luis")
    service.remember("me gusta el rock")

    reply = handler.handle(C(A.FORGET, "mi hermano"))

    assert reply.startswith("Olvidado, Jefe: mi hermano se llama Luis")
    assert "se puede recuperar" in reply
    assert len(service.list_memories().value) == 1

    storage.close()


def test_forget_without_matches_changes_nothing(tmp_path):
    handler, service, storage = create_handler(tmp_path)
    service.remember("me gusta el rock")

    reply = handler.handle(C(A.FORGET, "mi hermano"))

    assert reply == "No encuentro ningún recuerdo sobre eso, Jefe."
    assert len(service.list_memories().value) == 1

    storage.close()


def test_forget_with_several_matches_asks_for_detail(tmp_path):
    handler, service, storage = create_handler(tmp_path)
    service.remember("mi hermano se llama Luis")
    service.remember("mi hermano vive en Lima")

    reply = handler.handle(C(A.FORGET, "mi hermano"))

    assert "Encontré 2 recuerdos" in reply
    assert "más detalle" in reply
    assert len(service.list_memories().value) == 2

    storage.close()


def test_forget_this_removes_the_latest_memory(tmp_path):
    handler, service, storage = create_handler(tmp_path)
    service.remember("primero")
    service.remember("segundo")

    reply = handler.handle(C(A.FORGET, ""))

    assert reply.startswith("Olvidado, Jefe: segundo")

    storage.close()


def test_forget_this_with_an_empty_memory(tmp_path):
    handler, _, storage = create_handler(tmp_path)

    reply = handler.handle(C(A.FORGET, ""))

    assert reply == "No tengo nada guardado que olvidar, Jefe."

    storage.close()


def test_list_when_empty(tmp_path):
    handler, _, storage = create_handler(tmp_path)

    assert handler.handle(C(A.LIST)) == "Aún no tengo nada anotado, Jefe."
    assert handler.handle(C(A.LIST, "", "Música")) == (
        "No tengo nada anotado en «Música», Jefe."
    )

    storage.close()


def test_list_shows_memories_with_their_category(tmp_path):
    handler, service, storage = create_handler(tmp_path)
    service.remember("me gusta el rock", "Música")
    service.remember("trabajo de noche", "Trabajo")

    everything = handler.handle(C(A.LIST))
    only_music = handler.handle(C(A.LIST, "", "Música"))
    by_topic = handler.handle(C(A.LIST, "trabajo"))

    assert "- Música: me gusta el rock" in everything
    assert "- Trabajo: trabajo de noche" in everything
    assert "trabajo de noche" not in only_music
    assert "trabajo de noche" in by_topic

    storage.close()


def test_long_lists_are_cut_with_a_count(tmp_path):
    handler, service, storage = create_handler(tmp_path)

    for number in range(12):
        service.remember(f"dato número {number}")

    reply = handler.handle(C(A.LIST))

    assert "Y 2 más." in reply

    storage.close()