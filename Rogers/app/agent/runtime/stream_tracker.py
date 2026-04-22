from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from threading import Condition, Lock
from uuid import uuid4


@dataclass(frozen=True)
class StreamTrackedEvent:
    sequence_number: int
    event: str
    data: dict
    created_at: datetime


class _RunBuffer:
    def __init__(self, *, created_at: datetime) -> None:
        self.created_at = created_at
        self.events: list[StreamTrackedEvent] = []
        self.done = False


class StreamTracker:
    def __init__(self, *, ttl_seconds: int = 600, max_events_per_run: int = 2000) -> None:
        self._ttl = timedelta(seconds=ttl_seconds)
        self._max_events_per_run = max_events_per_run
        self._lock = Lock()
        self._cond = Condition(self._lock)
        self._runs: dict[str, _RunBuffer] = {}

    def create_run(self, *, session_id: str, user_id: int) -> str:
        run_id = f"run_{uuid4().hex[:16]}"
        with self._lock:
            self._gc_locked()
            self._runs[run_id] = _RunBuffer(created_at=datetime.now(timezone.utc))
        _ = session_id, user_id
        return run_id

    def append(self, *, run_id: str, event: str, sequence_number: int, data: dict) -> None:
        now = datetime.now(timezone.utc)
        with self._lock:
            self._gc_locked(now=now)
            if run_id not in self._runs:
                self._runs[run_id] = _RunBuffer(created_at=now)
            buf = self._runs[run_id]
            buf.events.append(StreamTrackedEvent(sequence_number=sequence_number, event=event, data=data, created_at=now))
            if len(buf.events) > self._max_events_per_run:
                buf.events[:] = buf.events[-self._max_events_per_run :]
            self._cond.notify_all()

    def mark_done(self, *, run_id: str) -> None:
        with self._lock:
            self._gc_locked()
            row = self._runs.get(run_id)
            if row is None:
                return
            row.done = True
            self._cond.notify_all()

    def is_done(self, *, run_id: str) -> bool:
        with self._lock:
            row = self._runs.get(run_id)
            if row is None:
                return True
            return row.done

    def replay_from(self, *, run_id: str, last_seq: int) -> list[StreamTrackedEvent]:
        with self._lock:
            self._gc_locked()
            row = self._runs.get(run_id)
            if row is None:
                return []
            return [e for e in row.events if e.sequence_number > last_seq]

    def wait_next(self, *, run_id: str, last_seq: int, timeout_seconds: float = 15.0) -> list[StreamTrackedEvent]:
        with self._lock:
            self._gc_locked()
            row = self._runs.get(run_id)
            if row is None:
                return []
            found = [e for e in row.events if e.sequence_number > last_seq]
            if found:
                return found
            if row.done:
                return []
            self._cond.wait(timeout=timeout_seconds)
            row = self._runs.get(run_id)
            if row is None:
                return []
            return [e for e in row.events if e.sequence_number > last_seq]

    def _gc_locked(self, *, now: datetime | None = None) -> None:
        now = now or datetime.now(timezone.utc)
        expired: list[str] = []
        for run_id, buf in self._runs.items():
            if now - buf.created_at > self._ttl:
                expired.append(run_id)
        for run_id in expired:
            self._runs.pop(run_id, None)
