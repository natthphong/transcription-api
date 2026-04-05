from __future__ import annotations

from typing import Any

from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class ApiError(Exception):
    def __init__(self, status_code: int, code: str, message: str, body: Any = None) -> None:
        self.status_code = status_code
        self.code = code
        self.message = message
        self.body = body
        super().__init__(message)


def envelope(body: Any, code: str = "OK", message: str = "success", meta: dict | None = None) -> dict:
    payload = {
        "code": code,
        "message": message,
        "body": body,
    }
    if meta is not None:
        payload["meta"] = meta
    return payload


def error_envelope(code: str, message: str, body: Any = None) -> dict:
    return {"code": code, "message": message, "body": body}


def success(body: Any, message: str = "success", code: str = "OK", status_code: int = 200) -> JSONResponse:
    return JSONResponse(status_code=status_code, content=envelope(body=body, code=code, message=message))


def created(body: Any, message: str) -> JSONResponse:
    return success(body=body, message=message, code="CREATED", status_code=201)


async def api_error_handler(_: Request, exc: ApiError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=error_envelope(code=exc.code, message=exc.message, body=exc.body),
    )


async def http_exception_handler(_: Request, exc: HTTPException) -> JSONResponse:
    message = exc.detail if isinstance(exc.detail, str) else "request failed"
    code = "INVALID_REQUEST" if exc.status_code < 500 else "INTERNAL_ERROR"
    return JSONResponse(
        status_code=exc.status_code,
        content=error_envelope(code=code, message=message, body=None),
    )


async def validation_exception_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    parts = []
    for item in exc.errors():
        loc = ".".join(str(piece) for piece in item.get("loc", []))
        msg = item.get("msg", "invalid")
        parts.append(f"{loc}: {msg}")
    message = "; ".join(parts) if parts else "invalid request"
    return JSONResponse(
        status_code=422,
        content=error_envelope(code="INVALID_REQUEST", message=message, body=None),
    )


async def unhandled_exception_handler(_: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content=error_envelope(code="INTERNAL_ERROR", message=str(exc) or "internal error", body=None),
    )
