from uuid import uuid4

import pytest

from terraforminator.domain.deployment import can_deploy
from terraforminator.domain.models import Review, ReviewResult


@pytest.mark.parametrize(
    "review_decision, approval_status, result",
    [
        ("approve", "pending", False),
        ("approve", "approved", True),
        ("approve", "rejected", False),
        ("needs_review", "pending", False),
        ("needs_review", "approved", True),
        ("needs_review", "rejected", False),
        ("block", "pending", False),
        ("block", "approved", False),
        ("block", "rejected", False),
    ],
)
def test_can_deploy(review_decision, approval_status, result):
    review = Review(
        review_id=uuid4(),
        result=ReviewResult(decision=review_decision, findings=()),
        plan_hash="hash",
        approval_status=approval_status,
    )
    assert can_deploy(review) == result
