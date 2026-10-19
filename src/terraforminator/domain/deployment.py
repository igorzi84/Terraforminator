from typing import Any

from terraforminator.domain.models import Review
from terraforminator.domain.plan_hash import hash_plan


def can_deploy(review: Review) -> bool:
    return (
        review.result.decision in ("approve", "needs_review")
        and review.approval_status == "approved"
    )


def can_deploy_plan(review: Review, plan: dict[str, Any]) -> bool:
    return hash_plan(plan) == review.plan_hash and can_deploy(review)
