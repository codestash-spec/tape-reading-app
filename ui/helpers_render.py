from __future__ import annotations

"""
Helper to coalesce UI updates and pause/resume rendering.
"""

from typing import Callable
from ui import helpers


def pause_on(widget) -> None:
    widget.installEventFilter(_PauseFilter(widget))


class _PauseFilter:
    def __init__(self, parent) -> None:
        self.parent = parent

    def eventFilter(self, obj, event):
        if event.type() in (event.MouseButtonPress, event.MouseMove):
            helpers.pause_render()
        elif event.type() == event.MouseButtonRelease:
            helpers.resume_render()
        return False
