from uuid import UUID

from terraforminator.domain.models import (
    ApprovalDecision,
    ApprovalRecord,
    ApprovalStatus,
)


def approve_review(status: ApprovalStatus) -> ApprovalDecision:
    if status != "pending":
        raise ValueError("Review is not pending.")
    return "approved"


def reject_review(status: ApprovalStatus) -> ApprovalDecision:
    if status != "pending":
        raise ValueError("Review is not pending.")
    return "rejected"


def record_approval(
    review_id: UUID, status: ApprovalStatus, reviewer: str, reason: str
) -> ApprovalRecord:
    return ApprovalRecord(
        review_id=review_id,
        status=approve_review(status),
        reviewer=reviewer,
        reason=reason,
    )


def record_rejection(
    review_id: UUID, status: ApprovalStatus, reviewer: str, reason: str
) -> ApprovalRecord:
    return ApprovalRecord(
        review_id=review_id,
        status=reject_review(status),
        reviewer=reviewer,
        reason=reason,
    )
