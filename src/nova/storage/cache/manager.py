import json
from pathlib import Path

from nova.storage.exceptions import CacheError


class CacheManager:
    """Manages disposable JSON cache files."""

    def __init__(self, cache_directory: Path) -> None:
        self.cache_directory = cache_directory

    def initialize(self) -> None:
        self.cache_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

    def set(self, key: str, value: object) -> None:
        try:
            self.initialize()

            path = self.cache_directory / f"{key}.json"

            path.write_text(
                json.dumps(value, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

        except (OSError, TypeError, ValueError) as exc:
            raise CacheError(
                f"Unable to write cache entry: {key}"
            ) from exc

    def get(self, key: str) -> object | None:
        try:
            path = self.cache_directory / f"{key}.json"

            if not path.exists():
                return None

            return json.loads(
                path.read_text(encoding="utf-8")
            )

        except (OSError, TypeError, ValueError) as exc:
            raise CacheError(
                f"Unable to read cache entry: {key}"
            ) from exc

    def delete(self, key: str) -> None:
        path = self.cache_directory / f"{key}.json"

        if path.exists():
            path.unlink()