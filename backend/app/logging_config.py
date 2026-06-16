from __future__ import annotations

import logging

from loguru import logger

from backend.app.config import get_settings


class InterceptHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        logger.opt(depth=6, exception=record.exc_info).log(record.levelname, record.getMessage())


def configure_logging() -> None:
    settings = get_settings()
    logging.basicConfig(handlers=[InterceptHandler()], level=settings.log_level, force=True)
    logger.remove()
    logger.add(lambda msg: print(msg, end=""), level=settings.log_level)
