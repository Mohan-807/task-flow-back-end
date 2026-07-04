from typing import TypeVar

from app.schemas.base import ApiResponse, ErrorDetail

T = TypeVar("T")


def success_response(
    message: str,
    data: T | None = None,
) -> ApiResponse[T]:
    return ApiResponse[T](
        success=True,
        message=message,
        data=data,
        errors=None,
    )


def error_response(
    message: str,
    errors: list[ErrorDetail] | None = None,
) -> ApiResponse[None]:
    return ApiResponse[None](
        success=False,
        message=message,
        data=None,
        errors=errors,
    )