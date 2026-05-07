from typing import Any, Dict
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from tortoise.exceptions import DoesNotExist, IntegrityError


class BusinessException(Exception):
    def __init__(self, code: int, message: str, data: Any = None):
        self.code = code
        self.message = message
        self.data = data


class NotFoundException(BusinessException):
    def __init__(self, message: str = "Resource not found", data: Any = None):
        super().__init__(code=404, message=message, data=data)


class UnauthorizedException(BusinessException):
    def __init__(self, message: str = "Unauthorized", data: Any = None):
        super().__init__(code=401, message=message, data=data)


class ForbiddenException(BusinessException):
    def __init__(self, message: str = "Forbidden", data: Any = None):
        super().__init__(code=403, message=message, data=data)


class BadRequestException(BusinessException):
    def __init__(self, message: str = "Bad request", data: Any = None):
        super().__init__(code=400, message=message, data=data)


async def business_exception_handler(request: Request, exc: BusinessException):
    return JSONResponse(
        status_code=exc.code,
        content={"code": exc.code, "message": exc.message, "data": exc.data},
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = []
    for error in exc.errors():
        errors.append(
            {
                "field": ".".join(str(loc) for loc in error["loc"]),
                "message": error["msg"],
                "type": error["type"],
            }
        )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"code": 422, "message": "Validation error", "data": {"errors": errors}},
    )


async def does_not_exist_handler(request: Request, exc: DoesNotExist):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"code": 404, "message": "Resource not found", "data": None},
    )


async def integrity_error_handler(request: Request, exc: IntegrityError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"code": 400, "message": "Database integrity error", "data": None},
    )


async def general_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"code": 500, "message": "Internal server error", "data": None},
    )


def setup_exception_handlers(app: FastAPI):
    app.add_exception_handler(BusinessException, business_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(DoesNotExist, does_not_exist_handler)
    app.add_exception_handler(IntegrityError, integrity_error_handler)
    app.add_exception_handler(Exception, general_exception_handler)
