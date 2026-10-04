"""Uniform API error body (PRD ТЗ№3 §50):

    {"error": {"code": "PRODUCT_OUT_OF_STOCK", "message": "...", "request_id": "..."},
     "detail": ...}

`detail` is kept exactly as FastAPI produced it so existing clients keep working; `error`
is the stable, machine-readable shape. Unhandled exceptions return a generic 500 and never
leak a stack trace (the traceback goes to the log, tagged with the same request id).
"""

import logging
import re
from typing import Any, Optional

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.request_id import new_request_id, request_id_var

logger = logging.getLogger("maru.errors")

_STATUS_CODES = {
    400: "BAD_REQUEST",
    401: "UNAUTHORIZED",
    402: "PAYMENT_REQUIRED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    405: "METHOD_NOT_ALLOWED",
    409: "CONFLICT",
    413: "PAYLOAD_TOO_LARGE",
    422: "VALIDATION_ERROR",
    429: "RATE_LIMITED",
    502: "BAD_GATEWAY",
    503: "SERVICE_UNAVAILABLE",
}

# Business errors are raised as "CODE: human message" (e.g. "INSUFFICIENT_STOCK: not enough ...").
_CODED_DETAIL = re.compile(r"^([A-Z][A-Z0-9_]{2,40}):\s*(.*)$", re.S)


def error_code_for(status_code: int, detail: Any) -> tuple[str, str]:
    """Returns (code, message) for a failed request."""
    if isinstance(detail, str):
        match = _CODED_DETAIL.match(detail)
        if match:
            return match.group(1), match.group(2) or match.group(1)
        message = detail
    elif isinstance(detail, list):
        message = "; ".join(str(d.get("msg", d)) if isinstance(d, dict) else str(d) for d in detail)
    else:
        message = "Request failed"
    code = _STATUS_CODES.get(status_code) or ("INTERNAL_ERROR" if status_code >= 500 else "REQUEST_FAILED")
    return code, message


def _body(status_code: int, detail: Any, request_id: Optional[str] = None) -> dict:
    code, message = error_code_for(status_code, detail)
    return {
        "detail": jsonable_encoder(detail),
        "error": {"code": code, "message": message, "request_id": request_id or request_id_var.get()},
    }


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(StarletteHTTPException)
    async def http_error(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        return JSONResponse(_body(exc.status_code, exc.detail), status_code=exc.status_code, headers=getattr(exc, "headers", None))

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(_body(422, exc.errors()), status_code=422)

    @app.exception_handler(Exception)
    async def unhandled_error(request: Request, exc: Exception) -> JSONResponse:
        # This handler sits outside the request-id middleware, so make sure the response
        # still carries an id the customer can quote and the log line can be matched to.
        request_id = request_id_var.get()
        if request_id == "-":
            request_id = new_request_id()
            request_id_var.set(request_id)
        logger.exception("Unhandled error on %s %s", request.method, request.url.path)
        generic = "Something went wrong. Please try again."
        return JSONResponse(_body(500, generic, request_id), status_code=500, headers={"X-Request-ID": request_id})
