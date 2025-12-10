from __future__ import annotations

import logging
import time
import uuid
from contextlib import contextmanager
from typing import Any, Dict, Optional

from telemetry.metrics import MetricsSink
from telemetry.tracing import TraceSpan


def new_trace_id() -> str:
    return uuid.uuid4().hex


def new_span_id() -> str:
    return uuid.uuid4().hex[:16]


@contextmanager
def traced_span(name: str, attributes: Optional[Dict[str, Any]] = None, metrics: Optional[MetricsSink] = None):
    span = TraceSpan(name=name, attributes=attributes or {})
    start = time.time()
    try:
        yield span
        duration = (time.time() - start) * 1000.0
        span.finish(duration_ms=duration, status="ok")
        if metrics:
            metrics.observe(f"span.{name}.duration_ms", duration)
    except Exception as exc:  # pragma: no cover - defensive
        duration = (time.time() - start) * 1000.0
        span.finish(duration_ms=duration, status="error", error=str(exc))
        logging.getLogger(__name__).exception("Span %s failed", name)
        if metrics:
            metrics.observe(f"span.{name}.errors", 1)
        raise
