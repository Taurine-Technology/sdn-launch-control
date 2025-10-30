import os
import threading
import time
from pathlib import Path


class _Tracer:
    def __init__(self):
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, name="obs-profiler", daemon=True)

    def start(self):
        if os.environ.get("PROFILING_MODE", "off").lower() == "tracemalloc":
            import tracemalloc  # noqa: WPS433
            tracemalloc.start(25)
            if not self._thread.is_alive():
                self._thread.start()

    def stop(self):
        self._stop.set()
        self._thread.join(timeout=2)

    def _run(self):
        import tracemalloc  # noqa: WPS433
        interval = int(os.environ.get("MEMORY_SNAPSHOT_INTERVAL_SEC", "600"))
        out_dir = Path(os.environ.get("PROFILES_DIR", "/usr/app/profiles"))
        out_dir.mkdir(parents=True, exist_ok=True)
        while not self._stop.is_set():
            time.sleep(interval)
            try:
                snap = tracemalloc.take_snapshot()
                ts = int(time.time())
                snap.dump(str(out_dir / f"tracemalloc-{ts}.bin"))
            except Exception:
                pass


_tracer = _Tracer()


def start_profiler_if_enabled():
    if os.environ.get("OBS_ENABLE", "true").lower() != "true":
        return
    if os.environ.get("PROFILING_MODE", "off").lower() == "tracemalloc":
        _tracer.start()


