import json
import logging
import sys
from datetime import datetime, timezone


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        extra = {}
        for k, v in record.__dict__.items():
            if k in {
                "name",
                "msg",
                "args",
                "levelname",
                "levelno",
                "pathname",
                "filename",
                "module",
                "exc_info",
                "exc_text",
                "stack_info",
                "lineno",
                "funcName",
                "created",
                "msecs",
                "relativeCreated",
                "thread",
                "threadName",
                "processName",
                "process",
            }:
                continue
            extra[k] = v
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            **extra,
        }
        return json.dumps(payload, ensure_ascii=True)


_logger = logging.getLogger("yt-clipper")
if not _logger.handlers:
    _logger.setLevel(logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    _logger.addHandler(handler)


def get_logger() -> logging.Logger:
    return _logger


def log_event(step: str, job_id: int | None = None, level: str = "info", **fields: object) -> None:
    logger = get_logger()
    extra = {"step": step}
    if job_id is not None:
        extra["job_id"] = job_id
    extra.update(fields)
    message = fields.pop("message", step)
    if level == "error":
        logger.error(message, extra=extra)
    elif level == "warning":
        logger.warning(message, extra=extra)
    else:
        logger.info(message, extra=extra)
