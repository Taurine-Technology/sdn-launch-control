import os
import threading
import time
from collections import deque
from typing import Deque, Dict, List, Tuple

from django.db import connections, DEFAULT_DB_ALIAS
from django.db.utils import OperationalError


class _InsertBatcher:
    def __init__(self, table: str, columns: Tuple[str, ...], maxlen: int = 5000, batch_size: int = 400, interval_s: float = 1.0):
        self.table = table
        self.columns = columns
        self.queue: Deque[Tuple] = deque(maxlen=maxlen)
        self.batch_size = batch_size
        self.interval_s = interval_s
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, name=f"obs-batcher-{table}", daemon=True)

    def start(self):
        if not self._thread.is_alive():
            self._thread.start()

    def stop(self):
        self._stop.set()
        self._thread.join(timeout=2)

    def put(self, row: Tuple):
        # Drop-oldest behavior via deque(maxlen)
        self.queue.append(row)

    def _flush(self, rows: List[Tuple]):
        if not rows:
            return
        sql_cols = ",".join(self.columns)
        placeholders = ",".join(["%s"] * len(self.columns))
        sql = f"INSERT INTO {self.table} ({sql_cols}) VALUES ({placeholders})"
        try:
            conn = connections[DEFAULT_DB_ALIAS]
            with conn.cursor() as cur:
                cur.executemany(sql, rows)
        except OperationalError:
            # Transient failure; drop batch to avoid blocking hot path
            pass

    def _run(self):
        while not self._stop.is_set():
            time.sleep(self.interval_s)
            rows: List[Tuple] = []
            while self.queue and len(rows) < self.batch_size:
                rows.append(self.queue.popleft())
            self._flush(rows)


_batchers: Dict[str, _InsertBatcher] = {}


def get_batcher(table: str, columns: Tuple[str, ...]) -> _InsertBatcher:
    key = f"{table}:{','.join(columns)}"
    batcher = _batchers.get(key)
    if batcher is None:
        batcher = _InsertBatcher(table=table, columns=columns)
        _batchers[key] = batcher
    return batcher


def start_default_batchers_if_enabled():
    if os.environ.get("OBS_ENABLE", "true").lower() != "true":
        return
    # api_requests batcher
    get_batcher(
        table="telemetry.api_requests",
        columns=("ts", "route", "method", "status", "bytes", "dur_ms", "host"),
    ).start()


