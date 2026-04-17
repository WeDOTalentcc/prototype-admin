"""
Structured JSON logging for production observability.

Provides JSON-formatted log output with consistent fields for
log aggregation services (ELK, CloudWatch, Datadog).

Usage:
    from app.shared.observability.structured_logging import setup_structured_logging
    
    setup_structured_logging(level="INFO", json_output=True)
"""
import json
import logging
from datetime import UTC, datetime
from typing import Any


class JSONFormatter(logging.Formatter):
    def __init__(self, service_name: str = "lia-agent-system"):
        super().__init__()
        self.service_name = service_name

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "service": self.service_name,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        if record.exc_info and record.exc_info[0]:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": self.formatException(record.exc_info),
            }

        if hasattr(record, "extra_data") and record.extra_data:
            log_entry["data"] = record.extra_data

        for key in ("request_id", "user_id", "tenant_id", "domain_id", "action_id", "trace_id", "span_id"):
            if hasattr(record, key):
                log_entry[key] = getattr(record, key)

        return json.dumps(log_entry, default=str, ensure_ascii=False)


class ContextLogger:
    def __init__(self, logger: logging.Logger, context: dict[str, Any] | None = None):
        self._logger = logger
        self._context = context or {}

    def _log(self, level: int, msg: str, **kwargs):
        extra = {**self._context, **kwargs}
        record = self._logger.makeRecord(
            self._logger.name, level, "(unknown file)", 0,
            msg, args=(), exc_info=None, extra=extra,
        )
        for key, value in extra.items():
            setattr(record, key, value)
        self._logger.handle(record)

    def info(self, msg: str, **kwargs):
        self._log(logging.INFO, msg, **kwargs)

    def warning(self, msg: str, **kwargs):
        self._log(logging.WARNING, msg, **kwargs)

    def error(self, msg: str, **kwargs):
        self._log(logging.ERROR, msg, **kwargs)

    def debug(self, msg: str, **kwargs):
        self._log(logging.DEBUG, msg, **kwargs)

    def with_context(self, **kwargs) -> 'ContextLogger':
        merged = {**self._context, **kwargs}
        return ContextLogger(self._logger, merged)


def get_context_logger(name: str, **initial_context) -> ContextLogger:
    logger = logging.getLogger(name)
    return ContextLogger(logger, initial_context)


def setup_structured_logging(
    level: str = "INFO",
    json_output: bool = True,
    service_name: str = "lia-agent-system",
) -> None:
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    handler = logging.StreamHandler()

    if json_output:
        handler.setFormatter(JSONFormatter(service_name=service_name))
    else:
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )

    root_logger.addHandler(handler)

    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
