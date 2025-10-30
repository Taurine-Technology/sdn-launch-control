import time
import logging
import inspect
from typing import Callable, Any

from asgiref.sync import async_to_sync
from django.http import HttpRequest, HttpResponse

from .batcher import get_batcher


logger = logging.getLogger(__name__)


class ApiMetricsMiddleware:
    def __init__(self, get_response: Callable[[HttpRequest], Any]):
        self.get_response = get_response
        self._batcher = get_batcher(
            table="telemetry.api_requests",
            columns=("ts", "route", "method", "status", "bytes", "dur_ms", "host"),
        )
        logger.info("ApiMetricsMiddleware initialized; batcher configured for telemetry.api_requests")

    def __call__(self, request: HttpRequest) -> HttpResponse:
        start = time.time()
        try:
            # Support both sync and async get_response
            if inspect.iscoroutinefunction(self.get_response):
                response = async_to_sync(self.get_response)(request)
            else:
                response = self.get_response(request)

            dur_ms = (time.time() - start) * 1000.0
            route = getattr(getattr(request, "resolver_match", None), "route", request.path)
            method = request.method
            status = getattr(response, "status_code", 0)
            # Content-Length from HttpResponse or headers mapping
            length_header = 0
            try:
                length_header = response.get("Content-Length", 0)  # type: ignore[attr-defined]
            except Exception:
                headers = getattr(response, "headers", {}) or {}
                length_header = headers.get("Content-Length", 0)
            length = int(length_header or 0)
            host = request.get_host()
            import datetime
            ts = datetime.datetime.utcnow()
            self._batcher.put((ts, route, method, status, length, dur_ms, host))
            logger.debug(
                "Enqueued API metric: route=%s method=%s status=%s dur_ms=%.2f bytes=%s host=%s",
                route,
                method,
                status,
                dur_ms,
                length,
                host,
            )
            return response
        except Exception:
            # Never break request path on metrics failure
            logger.warning("ApiMetricsMiddleware failed to enqueue metric", exc_info=True)
            # Best-effort: still return underlying response if available; otherwise pass through
            try:
                return response  # type: ignore[name-defined]
            except Exception:
                if inspect.iscoroutinefunction(self.get_response):
                    return async_to_sync(self.get_response)(request)
                return self.get_response(request)


