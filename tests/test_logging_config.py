import json
import logging
import sys

from terraforminator.logging_config import JsonFormatter


def test_formatter_includes_review_fields():
    fields = {
        "review_id": "review-123",
        "plan_hash": "hash-123",
        "policy_result": "approve",
        "approval_outcome": "approved",
    }
    logger = logging.getLogger("terraforminator.test")
    record = logger.makeRecord(
        name=logger.name,
        level=logging.INFO,
        fn=__file__,
        lno=0,
        msg="Human decision recorded",
        args=(),
        exc_info=None,
        extra=fields,
    )

    data = json.loads(JsonFormatter().format(record))

    assert data["level"] == "INFO"
    assert data["review_id"] == "review-123"
    assert data["plan_hash"] == "hash-123"
    assert data["policy_result"] == "approve"
    assert data["approval_outcome"] == "approved"


def test_formatter_does_not_include_non_existing_fields():
    logger = logging.getLogger("terraforminator.test")
    record = logger.makeRecord(
        name=logger.name,
        level=logging.INFO,
        fn=__file__,
        lno=0,
        msg="Human decision recorded",
        args=(),
        exc_info=None,
        extra=None,
    )

    data = json.loads(JsonFormatter().format(record))
    assert "review_id" not in data


def test_formatter_includes_exception():
    logger = logging.getLogger("terraforminator.test")

    try:
        raise ValueError("sample failure")
    except ValueError:
        record = logger.makeRecord(
            name=logger.name,
            level=logging.ERROR,
            fn=__file__,
            lno=0,
            msg="Review failed",
            args=(),
            exc_info=sys.exc_info(),
        )

    data = json.loads(JsonFormatter().format(record))
    assert "Traceback" in data["exception"]
    assert "ValueError: sample failure" in data["exception"]
