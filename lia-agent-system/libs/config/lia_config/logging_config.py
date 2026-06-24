"""
Structured JSON logging configuration for production.
"""
import json
import logging
import os
import sys
from datetime import datetime


class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        if hasattr(record, "request_id"):
            log_entry["request_id"] = record.request_id
        if hasattr(record, "user_id"):
            log_entry["user_id"] = record.user_id
        if record.exc_info and record.exc_info[0]:
            log_entry["exception"] = self.formatException(record.exc_info)
        if hasattr(record, "extra_data"):
            log_entry["data"] = record.extra_data
            
        return json.dumps(log_entry, default=str)


def configure_logging():
    """Configure structured logging based on environment."""
    env = os.getenv("APP_ENV", "development")
    log_level = os.getenv("LOG_LEVEL", "INFO")
    
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level, logging.INFO))
    
    root_logger.handlers.clear()
    
    handler = logging.StreamHandler(sys.stdout)

    if env == "production":
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        ))

    # PII masking no handler — garante cobertura de records propagados de child loggers,
    # que bypassam filtros do root logger e chegam diretamente nos handlers.
    try:
        from lia_pii import PIIMaskingFilter
        handler.addFilter(PIIMaskingFilter())
    except ImportError:
        pass

    root_logger.addHandler(handler)
    
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
