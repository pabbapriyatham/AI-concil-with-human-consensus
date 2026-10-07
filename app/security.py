import json
import logging
import os
import secrets
import time
from uuid import uuid4

from starlette.responses import JSONResponse

from app.tracing import request_context

log = logging.getLogger("mahthildis.http")


async def request_middleware(request, call_next):
    request_id = str(uuid4())
    token = request_context.set(request_id)
    started = time.perf_counter()
    try:
        key = os.getenv("API_TOKEN")
        if os.getenv("PUBLIC_DEPLOYMENT", "false").lower() == "true" and not key:
            return JSONResponse({"detail": "Public deployment requires API_TOKEN"}, status_code=503)
        if key and request.url.path.startswith("/api/") and request.method != "OPTIONS":
            supplied = request.headers.get("authorization", "").removeprefix("Bearer ")
            if not secrets.compare_digest(supplied, key):
                return JSONResponse({"detail": "Backend access token required"}, status_code=401)
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        log.info(
            json.dumps(
                {
                    "request_id": request_id,
                    "stage": "http",
                    "method": request.method,
                    "status": response.status_code,
                    "latency": time.perf_counter() - started,
                }
            )
        )
        return response
    finally:
        request_context.reset(token)
