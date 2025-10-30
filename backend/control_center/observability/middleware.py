import time
from typing import Callable
import datetime
from django.utils.deprecation import MiddlewareMixin
from django.http import HttpRequest, HttpResponse

from .batcher import get_batcher


class ApiMetricsMiddleware(MiddlewareMixin):
    def __init__(self, get_response: Callable):
        self.get_response = get_response
        self._batcher = get_batcher(
            table="telemetry.api_requests",
            columns=("ts", "route", "method", "status", "bytes", "dur_ms", "host"),
        )

    def __call__(self, request: HttpRequest) -> HttpResponse:
        start = time.time()
        response = self.get_response(request)
        try:
            dur_ms = (time.time() - start) * 1000.0
            route = getattr(getattr(request, "resolver_match", None), "route", request.path)
            method = request.method
            status = getattr(response, "status_code", 0)
            length = int(response.get("Content-Length", 0) or 0)
            host = request.get_host()
            # ts uses DB NOW(); push as None to use server time? We'll pass client time; DB expects timestamptz
            
            ts = datetime.datetime.utcnow()
            self._batcher.put((ts, route, method, status, length, dur_ms, host))
        except Exception:
            # Never break request path on metrics failure
            pass
        return response


