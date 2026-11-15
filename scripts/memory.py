"""Gestión de la memoria de NOVA desde la consola (Fase 6, D-029).

Ejecutar desde C:\\NOVA:
  python scripts/memory.py list [categoria]
  python scripts/memory.py all
  python scripts/memory.py add "texto" [--cat Música]
  python scripts/memory.py edit <id> "texto nuevo"
  python scripts/memory.py move <id> <categoria>
  python scripts/memory.py off <id>          desactiva (recuperable)
  python scripts/memory.py on <id>           reactiva
  python scripts/memory.py purge <id> --yes  borra definitivamente
  python scripts/memory.py audit

Los ids se escriben con sus primeros caracteres (los que muestra `list`).
"""

import argparse
import sys

from nova.memory import MemoryService
from nova.storage import StorageService
from nova.storage.paths import default_database_path


def print_memories(memories) -> None:
    if not memories:
        print("(sin recuerdos)")
        return

    for memory in memories:
        print(
            f"{str(memory.memory_id)[:8]}  {memory.status.value:8} "
            f"{memory.category:13} {memory.content}"
        )


def fail(result) -> int:
    print(f"ERROR {result.error.code}: {result.error.message}")

    return 1


def resolve(service: MemoryService, prefix: str):
    return service.resolve_id(prefix)


def run(args: argparse.Namespace, service: MemoryService) -> int:
    if args.command in ("list", "all"):
        result = service.list_memories(
            category=getattr(args, "category", None),
            include_inactive=args.command == "all",
        )

        if not result.success:
            return fail(result)

        print_memories(result.value)

        return 0

    if args.command == "add":
        result = service.remember(args.text, args.cat)

        if not result.success:
            return fail(result)

        print(f"Guardado en «{result.value.category}»: {result.value.memory_id}")

        return 0

    if args.command == "audit":
        result = service.audit()

        if not result.success:
            return fail(result)

        for entry in result.value:
            print(
                f"{entry['created_at'][:19]}  {entry['action']:20} "
                f"{entry['target_id'][:8]}  {entry['detail']}"
            )

        return 0

    resolved = resolve(service, args.id)

    if not resolved.success:
        return fail(resolved)

    memory_id = resolved.value

    if args.command == "edit":
        result = service.edit(memory_id, content=args.text)
    elif args.command == "move":
        result = service.edit(memory_id, category=args.category)
    elif args.command == "off":
        result = service.forget(memory_id)
    elif args.command == "on":
        result = service.reactivate(memory_id)
    else:
        if not args.yes:
            print("El borrado es definitivo: añade --yes para confirmarlo.")
            return 1

        result = service.purge(memory_id)

    if not result.success:
        return fail(result)

    print("Hecho.")

    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Memoria de NOVA")
    commands = parser.add_subparsers(dest="command", required=True)

    listing = commands.add_parser("list")
    listing.add_argument("category", nargs="?")

    commands.add_parser("all")

    add = commands.add_parser("add")
    add.add_argument("text")
    add.add_argument("--cat")

    edit = commands.add_parser("edit")
    edit.add_argument("id")
    edit.add_argument("text")

    move = commands.add_parser("move")
    move.add_argument("id")
    move.add_argument("category")

    for name in ("off", "on"):
        commands.add_parser(name).add_argument("id")

    purge = commands.add_parser("purge")
    purge.add_argument("id")
    purge.add_argument("--yes", action="store_true")

    commands.add_parser("audit")

    return parser


def main() -> int:
    args = build_parser().parse_args()

    storage = StorageService(default_database_path())
    storage.initialize()

    try:
        return run(args, MemoryService(storage.memory_repository))
    finally:
        storage.close()


if __name__ == "__main__":
    sys.exit(main())