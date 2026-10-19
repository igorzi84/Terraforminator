from terraforminator.domain.models import Review


def can_deploy(review: Review) -> bool:
    return (
        review.result.decision in ("approve", "needs_review")
        and review.approval_status == "approved"
    )
