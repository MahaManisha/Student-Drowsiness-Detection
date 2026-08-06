"""
Student Drowsiness Detection System - Centralized Logging Module

This module provides a production-grade, thread-safe logger that outputs formatted log
messages simultaneously to the terminal console and to rolling log files stored inside
the output/logs directory.
"""

import logging
from logging.handlers import RotatingFileHandler
import sys
from pathlib import Path

# Import log directory and log level settings from central config
from config import LOGS_DIR, LOG_LEVEL


class SafeRotatingFileHandler(RotatingFileHandler):
    """Windows-safe RotatingFileHandler that silently catches PermissionError during file rollover."""
    def doRollover(self) -> None:
        try:
            super().doRollover()
        except (PermissionError, OSError):
            pass


def setup_logger(name: str = "StudentDrowsinessDetection") -> logging.Logger:
    """
    Configures and returns a logger instance with console and rotating file handlers.
    """
    logger = logging.getLogger(name)

    # Resolve log level from config
    numeric_level = getattr(logging, str(LOG_LEVEL).upper(), logging.INFO)
    logger.setLevel(numeric_level)

    # Prevent adding duplicate handlers if setup_logger is called repeatedly
    if logger.hasHandlers():
        return logger

    # Ensure log directory exists
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    log_file_path = LOGS_DIR / "system.log"

    # Define standard log message format
    log_formatter = logging.Formatter(
        fmt="[%(asctime)s] [%(levelname)-8s] [%(name)s:%(lineno)d] - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # 1. Console Stream Handler (Outputs to terminal)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(log_formatter)
    logger.addHandler(console_handler)

    # 2. Safe Rotating File Handler (Saves to output/logs/system.log with 5MB rotation)
    file_handler = SafeRotatingFileHandler(
        filename=log_file_path,
        maxBytes=5 * 1024 * 1024,  # 5 MB per log file
        backupCount=5,             # Keep up to 5 backup log files
        encoding="utf-8"
    )
    file_handler.setLevel(numeric_level)
    file_handler.setFormatter(log_formatter)
    logger.addHandler(file_handler)

    return logger


def get_logger(module_name: str) -> logging.Logger:
    """
    Acquires a configured logger instance for any module in the system.

    Usage Example:
        from utils.logger import get_logger
        logger = get_logger(__name__)

        logger.info("Camera stream initialized.")
        logger.warning("Low light detected.")
        logger.error("Failed to read frame from video source.")
    """
    return setup_logger(module_name)
