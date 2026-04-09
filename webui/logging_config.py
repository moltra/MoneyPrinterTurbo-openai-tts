"""
Centralized logging configuration for WebUI

This module provides consistent logging setup across the WebUI application
with support for console output, file rotation, and configurable formatting.
"""
import sys
import os
from pathlib import Path
from typing import Optional
from loguru import logger

from app.config import config


def setup_webui_logging(
    log_to_file: Optional[bool] = None,
    file_path: Optional[str] = None,
    rotation: Optional[str] = None,
    retention: Optional[str] = None,
    level: Optional[str] = None
) -> None:
    """
    Configure logging for WebUI with rotation and formatting
    
    Args:
        log_to_file: Enable file logging (default: from config)
        file_path: Path to log file (default: ./storage/logs/webui.log)
        rotation: When to rotate log file (default: 500 MB)
        retention: How long to keep old logs (default: 30 days)
        level: Log level (default: from config.log_level)
    """
    # Remove default handler
    logger.remove()
    
    # Determine log level
    log_level = level or os.getenv("LOG_LEVEL") or config.log_level or "INFO"
    
    # Console logging with colors and formatting
    console_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>"
    )
    
    logger.add(
        sys.stdout,
        level=log_level,
        format=console_format,
        colorize=True,
        backtrace=True,
        diagnose=True,
    )
    
    # File logging (if enabled)
    enable_file_logging = (
        log_to_file 
        if log_to_file is not None 
        else config.app.get("log_file_enabled", False)
    )
    
    if enable_file_logging:
        # Determine file path
        default_log_path = "./storage/logs/webui.log"
        log_file_path = file_path or config.app.get("log_file_path", default_log_path)
        
        # Ensure log directory exists
        log_dir = Path(log_file_path).parent
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # File format (no colors)
        file_format = (
            "{time:YYYY-MM-DD HH:mm:ss} | "
            "{level: <8} | "
            "{name}:{function}:{line} - "
            "{message}"
        )
        
        # Rotation and retention settings
        log_rotation = rotation or config.app.get("log_rotation", "500 MB")
        log_retention = retention or config.app.get("log_retention", "30 days")
        
        logger.add(
            log_file_path,
            rotation=log_rotation,
            retention=log_retention,
            level=log_level,
            format=file_format,
            backtrace=True,
            diagnose=True,
            enqueue=True,  # Thread-safe logging
            compression="zip",  # Compress rotated logs
        )
        
        logger.info(f"File logging enabled: {log_file_path}")
    
    logger.info(f"Logging initialized at level: {log_level}")


def get_task_logger(task_id: str, log_to_file: bool = True) -> logger:
    """
    Create a logger bound to a specific task ID
    
    Args:
        task_id: Unique task identifier
        log_to_file: Whether to log to a task-specific file
        
    Returns:
        Logger instance bound to task context
    """
    task_logger = logger.bind(task_id=task_id)
    
    if log_to_file:
        # Add task-specific file handler
        task_log_path = f"./storage/logs/tasks/{task_id}.log"
        log_dir = Path(task_log_path).parent
        log_dir.mkdir(parents=True, exist_ok=True)
        
        file_format = (
            "{time:YYYY-MM-DD HH:mm:ss} | "
            "{level: <8} | "
            "{extra[task_id]} | "
            "{message}"
        )
        
        task_logger.add(
            task_log_path,
            format=file_format,
            level="DEBUG",
            rotation="10 MB",
            retention="7 days",
            filter=lambda record: record["extra"].get("task_id") == task_id,
        )
    
    return task_logger


def disable_logging():
    """Disable all logging (useful for tests)"""
    logger.remove()
    logger.disable("")


def enable_logging():
    """Re-enable logging after disabling"""
    logger.enable("")
    setup_webui_logging()


def log_system_info():
    """Log system and configuration information"""
    import platform
    import sys
    
    logger.info("=" * 60)
    logger.info("MoneyPrinterTurbo WebUI Starting")
    logger.info("=" * 60)
    logger.info(f"Project: {config.project_name}")
    logger.info(f"Version: {config.project_version}")
    logger.info(f"Python: {sys.version.split()[0]}")
    logger.info(f"Platform: {platform.system()} {platform.release()}")
    logger.info(f"Hostname: {config.hostname}")
    logger.info(f"Log Level: {config.log_level}")
    
    # Log mode (dev/prod)
    mode = os.getenv("MPT_MODE", "prod")
    logger.info(f"Mode: {mode.upper()}")
    
    logger.info("=" * 60)


# Initialize logging when module is imported
# This ensures consistent logging across the application
try:
    setup_webui_logging()
except Exception as e:
    # Fallback to basic logging if setup fails
    logger.error(f"Failed to setup logging: {e}")
    logger.add(sys.stderr, level="INFO")
