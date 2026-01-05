import pathlib
import sys
import logging
from enum import IntEnum
from typing import Union, Optional

class LogLevel(IntEnum):
    DEBUG = getattr(logging, "DEBUG")
    INFO = getattr(logging, "INFO")
    WARNING = getattr(logging, "WARNING")
    ERROR = getattr(logging, "ERROR")
    CRITICAL = getattr(logging, "CRITICAL")

DEFAULT_LOG_DIR = pathlib.Path("/var/tmp")
DEFAULT_LOG_FILE = DEFAULT_LOG_DIR / "ramalama-worker.log"

# Global logger
LOGGER_NAME = "ramalama-worker"
logger = logging.getLogger(LOGGER_NAME)

def configure_logger(lvl: LogLevel = LogLevel.WARNING, log_file: Optional[pathlib.Path] = DEFAULT_LOG_FILE) -> None:
    fmt = "%(asctime)s - %(levelname)s - %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"
    formatter = logging.Formatter(fmt, datefmt)
    handler: logging.Handler = None
    if log_file is not None:
        handler = logging.FileHandler(log_file)
    else:
        handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(lvl)
    handler.setFormatter(formatter)

    logging.basicConfig(
        handlers=[handler],
        datefmt=datefmt,
        level=lvl,
        format=fmt,
    )

def coerce_log_level(level: Union["LogLevel", str, int]) -> LogLevel:
    if isinstance(level, LogLevel):
        return level
    if isinstance(level, str):
        try:
            return LogLevel[level.upper()]
        except KeyError as exc:
            raise ValueError(f"Unsupported log level: {level}") from exc
    if isinstance(level, int):
        try:
            return LogLevel(level)
        except ValueError as exc:
            raise ValueError(f"Unsupported log level value: {level}") from exc
    raise TypeError(f"Cannot coerce {level!r} to LogLevel")
