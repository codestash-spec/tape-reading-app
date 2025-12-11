from __future__ import annotations

"""
Shared UI helpers for throttling and render pause (during drag/resize).
"""

UI_UPDATE_PAUSED: bool = False
FPS_MONITOR = None


def pause_render() -> None:
    global UI_UPDATE_PAUSED
    UI_UPDATE_PAUSED = True


def resume_render() -> None:
    global UI_UPDATE_PAUSED
    UI_UPDATE_PAUSED = False


def fps_tick() -> None:
    from ui.perf_monitor import FPSMonitor

    if isinstance(FPS_MONITOR, FPSMonitor):
        FPS_MONITOR.tick()
