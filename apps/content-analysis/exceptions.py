# FILE: apps/content-analysis/exceptions.py
from __future__ import annotations

from uuid import uuid4

from fastapi import Request
from fastapi.responses import JSONResponse
from types_shared import ErrorEnvelope


class ModuleProcessingError(Exception):
    def __init__(self, code: str, message: str, retryable: bool) -> None:
        self.code = code
        self.message = message
        self.retryable = retryable
        super().__init__(message)


class LocaleUncertainError(ModuleProcessingError):
    def __init__(self, message: str = "Language detection confidence below threshold") -> None:
        super().__init__(code="locale_uncertain", message=message, retryable=False)


async def module_exception_handler(_: Request, exc: ModuleProcessingError) -> JSONResponse:
    envelope = ErrorEnvelope(
        error={
            "code": exc.code,
            "message": exc.message,
            "retryable": exc.retryable,
            "trace_id": uuid4(),
        }
    )
    status = 422 if exc.code == "locale_uncertain" else 500
    return JSONResponse(status_code=status, content=envelope.model_dump(mode="json"))
