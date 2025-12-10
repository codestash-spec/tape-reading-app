from __future__ import annotations

import logging
from typing import Any, Dict

from core.logging import configure_logging


def get_logger(name: str, level: str = "INFO") -> logging.Logger:
    configure_logging(level)
    return logging.getLogger(name)


def log_json(logger: logging.Logger, level: str, message: str, **kwargs: Dict[str, Any]) -> None:
    extra = kwargs.get("extra", {})
    logger.log(getattr(logging, level.upper()), message, extra=extra)
