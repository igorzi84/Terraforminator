import json
import logging
from datetime import UTC, datetime


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created, UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for field in ("review_id", "plan_hash", "policy_result", "approval_outcome"):
            value = getattr(record, field, None)
            if value is not None:
                log_data[field] = value

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)


def configure_logging() -> None:
    logger = logging.getLogger("terraforminator")
    if logger.handlers:
        return

    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())

    logger.setLevel("INFO")
    logger.addHandler(handler)
    logger.propagate = False
