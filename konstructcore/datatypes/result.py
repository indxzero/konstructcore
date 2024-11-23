"""
Result[T] is a datatype that represents the result of a computation that may fail.
"""

from typing import Generic, TypeVar, Optional

T = TypeVar("T")


class Result(Generic[T]):
    """
    A datatype that represents the result of a computation that may fail.
    """

    def __init__(self, value: Optional[T] = None, error: Optional[Exception] = None):
        self.value = value
        self.error = error

    def is_ok(self) -> bool:
        """
        whether this result encapsulates the result from a successful computation
        """
        return self.error is None

    def is_err(self) -> bool:
        """
        whether this result encapsulates the error from a failed computation
        """
        return self.error is not None

    @classmethod
    def ok(cls, value: T) -> 'Result[Generic[T]]':
        """
        to directly construct an Ok value
        """
        return cls(value, error=None)

    @classmethod
    def err(cls, error: Exception) -> 'Result[Generic[T]]':
        """
        to directly construct an Err value
        """
        return cls(value=None, error=error)

    def __str__(self):
        if self.is_ok():
            return f'Ok({self.value})'
        else:
            return f'Err({self.error})'

    def __bool__(self):
        return self.is_ok()
