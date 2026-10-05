from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, field_validator

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


class ApprovalRequest(BaseModel):
    status: Literal["approved", "rejected"]
    reviewer: str
    reason: str

    @field_validator("reviewer", "reason")
    @classmethod
    def validate_empty_string(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Must not be blank")
        return value
