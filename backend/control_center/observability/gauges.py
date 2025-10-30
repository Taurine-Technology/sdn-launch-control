import os
import threading
import time
import gc
from typing import Optional

import psutil

from .batcher import get_batcher


class _GaugesSampler:
    def __init__(self, interval_s: float = 15.0):
        self.interval_s = interval_s
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, name="obs-gauges", daemon=True)
        self._proc = psutil.Process()
        self._api_batcher = get_batcher(
            table="telemetry.api_process_gauges",
            columns=("ts", "rss_mb", "heap_mb", "gc_gen0", "gc_gen1", "gc_gen2", "threads", "fds"),
        )
        self._pool_batcher = get_batcher(
            table="telemetry.db_pool_stats",
            columns=("ts", "size", "checked_in", "checked_out", "overflow"),
        )

    def start(self):
        if not self._thread.is_alive():
            self._thread.start()

    def stop(self):
        self._stop.set()
        self._thread.join(timeout=2)

    def _run(self):
        while not self._stop.is_set():
            try:
                import datetime
                ts = datetime.datetime.utcnow()
                mem = self._proc.memory_info().rss / (1024 * 1024)
                # Python heap approximation via gc.get_count and process memory
                # We don't have a simple heap number; use rss as primary, heap as 0.0 placeholder
                heap_mb = 0.0
                gc0, gc1, gc2 = gc.get_count()
                threads = self._proc.num_threads()
                try:
                    fds = self._proc.num_fds()
                except Exception:
                    fds = 0
                self._api_batcher.put((ts, mem, heap_mb, gc0, gc1, gc2, threads, fds))

                # Pool stats (best-effort)
                try:
                    from control_center.connection_pool_setup import get_pool_stats
                    stats = get_pool_stats()
                    default = (stats or {}).get('pools', {}).get('default')
                    if default:
                        self._pool_batcher.put(
                            (
                                ts,
                                default['size'],
                                default['checked_in'],
                                default['checked_out'],
                                default['overflow'],
                            )
                        )
                except Exception:
                    pass
            except Exception:
                pass
            time.sleep(self.interval_s)


_sampler: Optional[_GaugesSampler] = None


def start_gauges_if_enabled():
    if os.environ.get("OBS_ENABLE", "true").lower() != "true":
        return
    interval = float(os.environ.get("GAUGES_INTERVAL_SEC", "15"))
    global _sampler
    if _sampler is None:
        _sampler = _GaugesSampler(interval_s=interval)
        _sampler.start()


