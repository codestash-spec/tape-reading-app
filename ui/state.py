from __future__ import annotations


class UIState:
    """
    Shared UI state for render pausing/throttling.
    This avoids scattered globals across panels.
    """

    update_paused: bool = False

    @classmethod
    def set_paused(cls, value: bool) -> None:
        cls.update_paused = bool(value)

    @classmethod
    def is_paused(cls) -> bool:
        return cls.update_paused

