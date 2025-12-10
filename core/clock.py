from __future__ import annotations

import time
from datetime import datetime, timezone


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def monotonic_ms() -> float:
    return time.monotonic() * 1000.0
