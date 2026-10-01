from uuid import uuid4

import pytest

from terraforminator.domain.approval import (
    approve_review,
    record_approval,
    record_rejection,
    reject_review,
)


def test_approve_pending_review():
    assert approve_review("pending") == "approved"


@pytest.mark.parametrize("status", ["approved", "rejected"])
def test_approve_review_requires_pending_status(status):
    with pytest.raises(ValueError, match="Review is not pending"):
        approve_review(status)


def test_reject_pending_review():
    assert reject_review("pending") == "rejected"


@pytest.mark.parametrize("status", ["approved", "rejected"])
def test_reject_review_requires_pending_status(status):
    with pytest.raises(ValueError, match="Review is not pending"):
        reject_review(status)


def test_record_approval():
    review_id = uuid4()
    approval_record = record_approval(
        review_id=review_id, status="pending", reviewer="Igor", reason="Reason"
    )
    assert approval_record.review_id == review_id
    assert approval_record.status == "approved"
    assert approval_record.reviewer == "Igor"
    assert approval_record.reason == "Reason"


@pytest.mark.parametrize("status", ["approved", "rejected"])
def test_record_approval_requires_pending_status(status):
    with pytest.raises(ValueError):
        record_approval(
            review_id=uuid4(), status=status, reviewer="Igor", reason="Reason"
        )


def test_record_rejection():
    review_id = uuid4()
    approval_record = record_rejection(
        review_id=review_id, status="pending", reviewer="Igor", reason="Reason"
    )
    assert approval_record.review_id == review_id
    assert approval_record.status == "rejected"
    assert approval_record.reviewer == "Igor"
    assert approval_record.reason == "Reason"


@pytest.mark.parametrize("status", ["approved", "rejected"])
def test_record_rejection_requires_pending_status(status):
    with pytest.raises(ValueError):
        record_rejection(
            review_id=uuid4(), status=status, reviewer="Igor", reason="Reason"
        )
