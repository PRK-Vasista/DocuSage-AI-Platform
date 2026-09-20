# This is Copyright of DocuSage 2026 Owner Rohith Kumar Vasista P.

"""
Lightweight timing helpers for structured latency logs (stdlib only).
"""

import time


def monotonic_ms() -> float:
    """Return a high-resolution monotonic timestamp in milliseconds."""
    return time.perf_counter() * 1000.0


def duration_ms(started_ms: float) -> int:
    """
    Compute elapsed milliseconds since started_ms.

    Args:
        started_ms: Value previously returned by monotonic_ms().

    Returns:
        int: Non-negative elapsed duration in whole milliseconds.
    """
    elapsed = int(monotonic_ms() - started_ms)
    return max(0, elapsed)
