"""Logging configuration for the auto-evaluation tool"""

import logging
import sys
from pathlib import Path
from datetime import datetime


def setup_logger(
    name: str = "auto_eval",
    log_level: int = logging.INFO,
    log_dir: str = "logs",
    console_output: bool = True
) -> logging.Logger:
    """
    Set up logger with file and console handlers

    Args:
        name: Logger name
        log_level: Logging level
        log_dir: Directory for log files
        console_output: Whether to output to console

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(log_level)

    # Avoid duplicate handlers
    if logger.handlers:
        return logger

    # Create log directory if it doesn't exist
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)

    # File handler with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_handler = logging.FileHandler(
        log_path / f"auto_eval_{timestamp}.log",
        encoding='utf-8'
    )
    file_handler.setLevel(log_level)

    # Console handler
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)

    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    if console_output:
        console_handler.setFormatter(formatter)

    # Add handlers
    logger.addHandler(file_handler)
    if console_output:
        logger.addHandler(console_handler)

    return logger
