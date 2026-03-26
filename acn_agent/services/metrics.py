from __future__ import annotations

from collections import Counter


class MetricsRegistry:
    """Simple in-memory counters for observability."""

    def __init__(self) -> None:
        self._counters: Counter[str] = Counter()

    def increment(self, key: str) -> None:
        """Increment a counter."""
        self._counters[key] += 1

    def snapshot(self) -> dict[str, int]:
        """Get current metric values."""
        return dict(self._counters)

    def reset(self) -> None:
        """Reset all counters."""
        self._counters.clear()
