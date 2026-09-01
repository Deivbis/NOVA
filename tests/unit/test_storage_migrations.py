import sqlite3

from nova.storage.migrations.runner import MigrationRunner
from nova.storage.migrations.versions import v001_initial


def test_initial_migration_creates_schema(tmp_path) -> None:
    database = tmp_path / "nova.db"

    connection = sqlite3.connect(database)

    runner = MigrationRunner(connection)

    assert runner.current_version() == 0

    v001_initial.apply(connection)
    runner.set_version(v001_initial.VERSION)

    assert runner.current_version() == 1

    table = connection.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        AND name = 'app_state'
        """
    ).fetchone()

    assert table is not None

    connection.close()