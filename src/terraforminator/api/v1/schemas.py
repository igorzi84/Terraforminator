from typing import Any
from uuid import UUID

from pydantic import BaseModel

from terraforminator.domain.models import ApprovalStatus, ReviewDecision, Severity


class FindingResponse(BaseModel):
    id: str
    severity: Severity
    resource_address: str
    evidence: str
    remediation: str


class ReviewRequest(BaseModel):
    plan: dict[str, Any]


class ReviewResponse(BaseModel):
    review_id: UUID
    decision: ReviewDecision
    findings: list[FindingResponse]
    explanation: str


class StoredReviewResponse(BaseModel):
    review_id: UUID
    decision: ReviewDecision
    findings: list[FindingResponse]
    approval_status: ApprovalStatus
