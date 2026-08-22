from dataclasses import dataclass
from typing import Generic, TypeVar


T = TypeVar("T")


@dataclass(frozen=True)
class Failure:
    code: str
    message: str


@dataclass(frozen=True)
class Result(Generic[T]):
    success: bool
    value: T | None = None
    error: Failure | None = None

    @classmethod
    def ok(cls, value: T | None = None) -> "Result[T]":
        return cls(
            success=True,
            value=value,
            error=None,
        )

    @classmethod
    def fail(
        cls,
        code: str,
        message: str,
    ) -> "Result[T]":
        return cls(
            success=False,
            value=None,
            error=Failure(
                code=code,
                message=message,
            ),
        )