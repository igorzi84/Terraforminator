from uuid import uuid4

import pytest

from terraforminator.domain.deployment import can_deploy, can_deploy_plan
from terraforminator.domain.models import Review, ReviewResult
from terraforminator.domain.plan_hash import hash_plan


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


@pytest.mark.parametrize(
    "policy_decision, approval_status, plan_matches, expected",
    [
        ("approve", "approved", True, True),
        ("approve", "approved", False, False),
        ("approve", "pending", True, False),
        ("block", "approved", True, False),
    ],
)
def test_can_deploy_plan(policy_decision, approval_status, plan_matches, expected):
    original_plan = {"resource_changes": []}
    review = Review(
        review_id=uuid4(),
        result=ReviewResult(decision=policy_decision, findings=()),
        plan_hash=hash_plan(original_plan),
        approval_status=approval_status,
    )

    candidate_plan = (
        original_plan
        if plan_matches
        else {"resource_changes": [], "terraform_version": "different"}
    )

    assert can_deploy_plan(review, candidate_plan) is expected
