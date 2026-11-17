import sqlite3

from nova.storage.exceptions import MigrationError

VERSION = 4


def apply(connection: sqlite3.Connection) -> None:
    """Candidatos de aprendizaje y observaciones (SPEC-006)."""
    try:
        connection.execute(
            """
            CREATE TABLE learning_candidates (
                id TEXT PRIMARY KEY,
                key TEXT NOT NULL UNIQUE,
                kind TEXT NOT NULL CHECK (kind IN ('explicit', 'pattern')),
                category TEXT NOT NULL,
                content TEXT NOT NULL,
                evidence INTEGER NOT NULL DEFAULT 1,
                asked INTEGER NOT NULL DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'pending'
                    CHECK (status IN ('pending', 'confirmed', 'rejected')),
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        # Solo el tema (categoría); nunca el texto del mensaje.
        connection.execute(
            """
            CREATE TABLE learning_observations (
                id TEXT PRIMARY KEY,
                topic TEXT NOT NULL,
                conversation_id TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE INDEX idx_learning_obs_topic
            ON learning_observations(topic, created_at)
            """
        )
    except sqlite3.Error as exc:
        raise MigrationError(
            "Unable to apply learning migration."
        ) from exc