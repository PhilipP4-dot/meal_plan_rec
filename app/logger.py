"""
Logging configuration for the meal plan recommendation system.
"""
import logging
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


class JsonFormatter(logging.Formatter):
    """Format application logs as one JSON object per line."""

    _CONTEXT_FIELDS = (
        "request_id",
        "method",
        "path",
        "status_code",
        "duration_ms",
    )

    def format(self, record):
        event = {
            "timestamp": datetime.fromtimestamp(record.created, timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for field in self._CONTEXT_FIELDS:
            value = getattr(record, field, None)
            if value is not None:
                event[field] = value

        if record.exc_info:
            event["exception"] = self.formatException(record.exc_info)

        return json.dumps(event, default=str)


def setup_logging(log_level=logging.INFO, log_file=None):
    """
    Configure logging for the application.
    
    Args:
        log_level: Logging level (default: INFO)
        log_file: Optional file path for logging output
    """
    # Create logs directory if needed
    if log_file:
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
    
    handlers = [logging.StreamHandler(sys.stdout)]
    if log_file:
        handlers.append(logging.FileHandler(log_file))

    formatter = JsonFormatter()
    for handler in handlers:
        handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    if not root_logger.handlers:
        root_logger.addHandler(handlers[0])
        for handler in handlers[1:]:
            root_logger.addHandler(handler)
    
    # Set levels for noisy third-party libraries
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy').setLevel(logging.WARNING)

def get_logger(name):
    """
    Get a logger for a specific module.
    
    Args:
        name: Usually __name__ from the calling module
        
    Returns:
        logging.Logger instance
    """
    return logging.getLogger(name)
