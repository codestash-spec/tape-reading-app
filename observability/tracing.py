from __future__ import annotations

import contextlib
from typing import Iterator, Optional


@contextlib.contextmanager
def span(name: str, trace_id: Optional[str] = None) -> Iterator[str]:
    # Placeholder for OTLP integration; returns span_id
    span_id = f"span-{name}"
    yield span_id
