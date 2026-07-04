from fastapi import FastAPI, status
from fastapi.responses import JSONResponse
from app.core.responses import error_response
from fastapi.exceptions import RequestValidationError
from app.schemas.base import ErrorDetail

from app.core.exceptions import UserNotFoundException


def register_exception_handlers(app: FastAPI):
    @app.exception_handler(UserNotFoundException)
    async def user_not_found_exception_handler(request, exc):
       return JSONResponse(
             status_code=status.HTTP_404_NOT_FOUND,
             content=error_response(
             message=exc.message,
             ).model_dump(),
             )
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request, exc: RequestValidationError):
        errors = []

        for error in exc.errors():
         errors.append(
            ErrorDetail(
                field=".".join(str(item) for item in error["loc"][1:]),
                message=error["msg"],
            )
        )

         return JSONResponse(
             status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
             content=error_response(
             message="Validation failed",
             errors=errors,
        ).model_dump(),
    )