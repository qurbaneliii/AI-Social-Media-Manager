# FILE: apps/visual-understanding/exceptions.py
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


async def module_exception_handler(_: Request, exc: ModuleProcessingError) -> JSONResponse:
    envelope = ErrorEnvelope(
        error={
            "code": exc.code,
            "message": exc.message,
            "retryable": exc.retryable,
            "trace_id": uuid4(),
        }
    )
    return JSONResponse(status_code=500, content=envelope.model_dump(mode="json"))
