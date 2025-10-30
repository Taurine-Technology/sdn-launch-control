import os
import time
from typing import Dict

from celery.signals import task_prerun, task_postrun

from .batcher import get_batcher


_task_started_at: Dict[str, float] = {}
_batcher = get_batcher(
    table="telemetry.celery_tasks",
    columns=("ts", "task", "status", "dur_ms", "rss_before_mb", "rss_after_mb"),
)


def _rss_mb() -> float:
    try:
        import psutil
        return psutil.Process().memory_info().rss / (1024 * 1024)
    except Exception:
        return 0.0


@task_prerun.connect
def _on_task_start(sender=None, task_id=None, task=None, **kwargs):  # noqa: D401
    if os.environ.get("OBS_ENABLE", "true").lower() != "true":
        return
    _task_started_at[task_id] = time.time()
    # Store starting RSS as a side channel using batcher after completion for consistency.


@task_postrun.connect
def _on_task_done(sender=None, task_id=None, task=None, state=None, **kwargs):
    if os.environ.get("OBS_ENABLE", "true").lower() != "true":
        return
    try:
        import datetime
        ts = datetime.datetime.utcnow()
        start = _task_started_at.pop(task_id, None)
        dur_ms = ((time.time() - start) * 1000.0) if start else 0.0
        after = _rss_mb()
        _batcher.put((ts, sender.name if sender else "unknown", state or "unknown", dur_ms, None, after))
    except Exception:
        pass


