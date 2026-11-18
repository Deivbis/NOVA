"""Puente al hilo de la UI: SQLite solo se usa allí."""

from collections.abc import Callable
from typing import Any


class MainThread:
    def __init__(self) -> None:
        self._call: Callable | None = None
        self._post: Callable | None = None

    def bind(self, call: Callable | None, post: Callable | None) -> None:
        self._call, self._post = call, post

    def call(self, fn: Callable[[], Any]) -> Any:
        """Ejecuta `fn` en el hilo de la UI y espera su resultado."""
        return fn() if self._call is None else self._call(fn)

    def post(self, fn: Callable[[], None]) -> None:
        """Ejecuta `fn` en el hilo de la UI sin esperar."""
        if self._post is None:
            fn()
        else:
            self._post(fn)