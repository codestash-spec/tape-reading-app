from __future__ import annotations

import time
from typing import Iterable, Iterator, Tuple


def paced_events(events: Iterable[Tuple[float, object]], speed: float = 1.0) -> Iterator[object]:
    """
    Yield events at their original pacing adjusted by speed.
    events: iterable of (timestamp_seconds, event)
    """
    prev_ts = None
    for ts, evt in events:
        if prev_ts is not None:
            delay = (ts - prev_ts) / max(speed, 0.0001)
            if delay > 0:
                time.sleep(delay)
        prev_ts = ts
        yield evt
