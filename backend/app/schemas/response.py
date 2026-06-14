from typing import Any, Optional
from pydantic import BaseModel


class Response(BaseModel):
    code: int = 0
    message: str = "success"
    data: Optional[Any] = None


def success(data: Any = None, message: str = "success") -> Response:
    return Response(code=0, message=message, data=data)


def fail(message: str, code: int = 1, data: Any = None) -> Response:
    return Response(code=code, message=message, data=data)
