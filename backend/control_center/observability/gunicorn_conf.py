import datetime
import os

from .batcher import get_batcher


_batcher = get_batcher(
    table="telemetry.gunicorn_events",
    columns=("ts", "event", "worker_pid"),
)


def post_worker_init(worker):
    try:
        if os.environ.get("OBS_ENABLE", "true").lower() != "true":
            return
        _batcher.put((datetime.datetime.utcnow(), "worker_init", worker.pid))
    except Exception:
        pass


def worker_exit(server, worker):
    try:
        if os.environ.get("OBS_ENABLE", "true").lower() != "true":
            return
        _batcher.put((datetime.datetime.utcnow(), "worker_exit", worker.pid))
    except Exception:
        pass


