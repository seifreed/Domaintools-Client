"""Structured logging utilities."""

import json
import logging
import logging.config
import time
from pathlib import Path
from typing import Any, Dict, Optional


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_entry = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add extra fields if present
        if hasattr(record, "extra"):
            log_entry.update(record.extra)

        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry)


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[Path] = None,
    json_format: bool = False,
    enable_console: bool = True,
) -> None:
    """Setup structured logging configuration.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path
        json_format: Use JSON formatting
        enable_console: Enable console logging
    """
    config: Dict[str, Any] = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {"format": "%(asctime)s [%(levelname)8s] %(name)s: %(message)s"},
            "detailed": {
                "format": "%(asctime)s [%(levelname)8s] %(name)s:%(funcName)s:%(lineno)d: %(message)s"
            },
            "json": {
                "()": JSONFormatter,
            },
        },
        "handlers": {},
        "loggers": {"domaintools_client": {"level": log_level, "handlers": [], "propagate": False}},
        "root": {"level": log_level, "handlers": []},
    }

    # Console handler
    if enable_console:
        config["handlers"]["console"] = {
            "class": "logging.StreamHandler",
            "level": log_level,
            "formatter": "json" if json_format else "standard",
            "stream": "ext://sys.stdout",
        }
        config["loggers"]["domaintools_client"]["handlers"].append("console")
        config["root"]["handlers"].append("console")

    # File handler
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        config["handlers"]["file"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "level": log_level,
            "formatter": "json" if json_format else "detailed",
            "filename": str(log_file),
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
            "encoding": "utf8",
        }
        config["loggers"]["domaintools_client"]["handlers"].append("file")
        config["root"]["handlers"].append("file")

    logging.config.dictConfig(config)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for the given name.

    Args:
        name: Logger name

    Returns:
        Configured logger instance
    """
    return logging.getLogger(f"domaintools_client.{name}")


def log_api_request(
    logger: logging.Logger,
    endpoint: str,
    domain: Optional[str] = None,
    response_time: Optional[float] = None,
    status_code: Optional[int] = None,
    error: Optional[str] = None,
) -> None:
    """Log API request with structured data.

    Args:
        logger: Logger instance
        endpoint: API endpoint name
        domain: Domain being queried (if applicable)
        response_time: Response time in seconds
        status_code: HTTP status code
        error: Error message if request failed
    """
    extra = {
        "endpoint": endpoint,
        "domain": domain,
        "response_time": response_time,
        "status_code": status_code,
    }

    if error:
        logger.error(f"API request failed: {error}", extra={"extra": extra})
    else:
        logger.info(f"API request completed: {endpoint}", extra={"extra": extra})


def log_performance(
    logger: logging.Logger,
    operation: str,
    duration: float,
    success: bool = True,
    metadata: Optional[Dict[str, Any]] = None,
) -> None:
    """Log performance metrics.

    Args:
        logger: Logger instance
        operation: Operation name
        duration: Duration in seconds
        success: Whether operation was successful
        metadata: Additional metadata
    """
    extra = {
        "operation": operation,
        "duration": duration,
        "success": success,
        "metadata": metadata or {},
    }

    level = logging.INFO if success else logging.WARNING
    message = f"Performance: {operation} took {duration:.3f}s"

    logger.log(level, message, extra={"extra": extra})


class RequestLogger:
    """Context manager for logging API requests."""

    def __init__(self, logger: logging.Logger, endpoint: str, domain: Optional[str] = None):
        """Initialize request logger.

        Args:
            logger: Logger instance
            endpoint: API endpoint name
            domain: Domain being queried
        """
        self.logger = logger
        self.endpoint = endpoint
        self.domain = domain
        self.start_time: Optional[float] = None

    def __enter__(self):
        """Start timing the request."""
        self.start_time = time.time()
        self.logger.debug(f"Starting API request: {self.endpoint}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Log request completion."""
        duration = time.time() - self.start_time if self.start_time else 0

        if exc_type is None:
            log_api_request(self.logger, self.endpoint, domain=self.domain, response_time=duration)
        else:
            log_api_request(
                self.logger,
                self.endpoint,
                domain=self.domain,
                response_time=duration,
                error=str(exc_val),
            )


class PerformanceLogger:
    """Context manager for performance logging."""

    def __init__(
        self, logger: logging.Logger, operation: str, metadata: Optional[Dict[str, Any]] = None
    ):
        """Initialize performance logger.

        Args:
            logger: Logger instance
            operation: Operation name
            metadata: Additional metadata
        """
        self.logger = logger
        self.operation = operation
        self.metadata = metadata or {}
        self.start_time: Optional[float] = None

    def __enter__(self):
        """Start timing the operation."""
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Log operation completion."""
        duration = time.time() - self.start_time if self.start_time else 0
        success = exc_type is None

        log_performance(
            self.logger, self.operation, duration, success=success, metadata=self.metadata
        )
