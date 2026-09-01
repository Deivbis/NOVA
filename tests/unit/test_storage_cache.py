from nova.storage.cache.manager import CacheManager


def test_cache_can_store_and_read_value(tmp_path) -> None:
    cache = CacheManager(tmp_path)

    cache.set(
        "test",
        {"nova": "online"},
    )

    assert cache.get("test") == {
        "nova": "online",
    }


def test_cache_can_delete_value(tmp_path) -> None:
    cache = CacheManager(tmp_path)

    cache.set(
        "test",
        {"value": 1},
    )

    cache.delete("test")

    assert cache.get("test") is None