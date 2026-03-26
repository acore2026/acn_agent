from __future__ import annotations

from threading import Lock

from acn_agent.models.common import PipelineLog, ProxyRecord


class StateStore:
    """Thread-safe in-memory storage for local agent state."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._records: list[ProxyRecord] = []
        self._pipeline_logs: list[PipelineLog] = []

    def add_record(self, record: ProxyRecord) -> None:
        """Persist a proxy record."""
        with self._lock:
            self._records.append(record)

    def add_pipeline_log(self, log_item: PipelineLog) -> None:
        """Persist a pipeline log."""
        with self._lock:
            self._pipeline_logs.append(log_item)

    def list_records(self) -> list[ProxyRecord]:
        """Return all proxy records."""
        with self._lock:
            return list(self._records)

    def list_pipeline_logs(self) -> list[PipelineLog]:
        """Return all pipeline logs."""
        with self._lock:
            return list(self._pipeline_logs)

    def clear(self) -> tuple[int, int]:
        """Clear all local state and return cleared counts."""
        with self._lock:
            record_count = len(self._records)
            pipeline_log_count = len(self._pipeline_logs)
            self._records.clear()
            self._pipeline_logs.clear()
        return record_count, pipeline_log_count
