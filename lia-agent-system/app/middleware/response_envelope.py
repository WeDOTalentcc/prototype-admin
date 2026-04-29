import json
import logging
import os
from datetime import datetime, timezone

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response, StreamingResponse

logger = logging.getLogger(__name__)

_DISABLED = os.environ.get("LIA_DISABLE_ENVELOPE_MIDDLEWARE", "0") == "1"

_BYPASS_PREFIXES = ("/ws", "/health", "/docs", "/openapi", "/redoc", "/metrics")


class ResponseEnvelopeMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if _DISABLED:
            return await call_next(request)

        path = request.url.path
        if any(path.startswith(prefix) for prefix in _BYPASS_PREFIXES):
            return await call_next(request)

        response = await call_next(request)

        if not (200 <= response.status_code < 300):
            return response

        content_type = response.headers.get("content-type", "")
        if "application/json" not in content_type:
            return response

        body_parts = []
        async for chunk in response.body_iterator:
            if isinstance(chunk, bytes):
                body_parts.append(chunk)
            else:
                body_parts.append(chunk.encode("utf-8"))
        raw = b"".join(body_parts)

        try:
            data = json.loads(raw)
        except (json.JSONDecodeError, ValueError):
            return Response(content=raw, status_code=response.status_code, headers=dict(response.headers))

        if isinstance(data, dict) and "ok" in data:
            return Response(content=raw, status_code=response.status_code, headers=dict(response.headers))

        request_id = getattr(request.state, "request_id", None)
        envelope = {
            "ok": True,
            "data": data,
            "meta": {
                "request_id": request_id,
                "ts": datetime.now(timezone.utc).isoformat(),
            },
        }

        wrapped = json.dumps(envelope, ensure_ascii=False)
        headers = dict(response.headers)
        headers["content-length"] = str(len(wrapped.encode("utf-8")))
        return Response(content=wrapped, status_code=response.status_code, headers=headers, media_type="application/json")
