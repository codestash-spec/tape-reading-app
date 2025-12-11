from __future__ import annotations

"""
Shared UI helpers for throttling and render pause (during drag/resize).
"""

from ui.state import UIState

FPS_MONITOR = None
_fps_samples = []
_fps_last = None


def pause_render() -> None:
    UIState.set_paused(True)


def resume_render() -> None:
    UIState.set_paused(False)


def is_paused() -> bool:
    return UIState.is_paused()


def fps_tick() -> None:
    global _fps_last, _fps_samples
    from ui.perf_monitor import FPSMonitor

    if isinstance(FPS_MONITOR, FPSMonitor):
        FPS_MONITOR.tick()
    import time

    now = time.time()
    if _fps_last is None:
        _fps_last = now
        return
    dt = now - _fps_last
    _fps_last = now
    if dt > 0:
        _fps_samples.append(1.0 / dt)
        if len(_fps_samples) > 240:
            _fps_samples = _fps_samples[-240:]


def fps_value() -> float:
    if not _fps_samples:
        return 0.0
    return sum(_fps_samples) / len(_fps_samples)
