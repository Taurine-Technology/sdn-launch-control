import os
import threading
import time
from .batcher import get_batcher


_conns = 0
_groups = 0
_lock = threading.Lock()


def connection_opened():
    global _conns
    with _lock:
        _conns += 1


def connection_closed():
    global _conns
    with _lock:
        _conns = max(0, _conns - 1)


def group_joined():
    global _groups
    with _lock:
        _groups += 1


def group_left():
    global _groups
    with _lock:
        _groups = max(0, _groups - 1)


class _ChannelsFlusher:
    def __init__(self, interval_s: float = 15.0):
        self.interval_s = interval_s
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, name="obs-channels", daemon=True)
        self._batcher = get_batcher(
            table="telemetry.channels_stats",
            columns=("ts", "conns", "groups", "msgs_per_s"),
        )

    def start(self):
        if not self._thread.is_alive():
            self._thread.start()

    def stop(self):
        self._stop.set()
        self._thread.join(timeout=2)

    def _run(self):
        prev_msgs = 0.0
        while not self._stop.is_set():
            try:
                import datetime
                with _lock:
                    conns = _conns
                    groups = _groups
                ts = datetime.datetime.utcnow()
                msgs_per_s = 0.0  # Placeholder; can be wired later from app metrics
                self._batcher.put((ts, conns, groups, msgs_per_s))
            except Exception:
                pass
            time.sleep(self.interval_s)


_flusher: _ChannelsFlusher | None = None


def start_channels_flusher_if_enabled():
    if os.environ.get("OBS_ENABLE", "true").lower() != "true":
        return
    global _flusher
    if _flusher is None:
        _flusher = _ChannelsFlusher()
        _flusher.start()


