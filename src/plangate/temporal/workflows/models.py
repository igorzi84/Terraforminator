from dataclasses import dataclass

from plangate.domain.models import ReviewDecision


@dataclass(frozen=True)
class ApprovalWorkflowInput:
    review_id: str
    policy_result: ReviewDecision
