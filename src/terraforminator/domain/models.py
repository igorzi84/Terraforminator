from dataclasses import dataclass
from typing import Any, Literal
from uuid import UUID

ChangeAction = Literal["create", "update", "delete", "no-op", "read"]
Severity = Literal["low", "medium", "high"]
ReviewDecision = Literal["approve", "needs_review", "block"]
ApprovalStatus = Literal["pending", "approved", "rejected"]
ApprovalDecision = Literal["approved", "rejected"]


@dataclass(frozen=True)
class ResourceChange:
    address: str
    resource_type: str
    name: str
    actions: tuple[ChangeAction, ...]
    before: dict[str, Any] | None
    after: dict[str, Any] | None
    after_unknown: dict[str, Any] | None = None


@dataclass(frozen=True)
class Finding:
    id: str
    severity: Severity
    resource_address: str
    evidence: str
    remediation: str


@dataclass(frozen=True)
class PolicyConfig:
    enabled_policy_ids: frozenset[str] = frozenset(
        {
            "public-inbound-access",
            "iam-wildcard-permission",
            "destructive-stateful-change",
            "storage-encryption",
            "missing-required-tags",
        }
    )
    required_tags: frozenset[str] = frozenset({"Project", "Environment", "Owner"})


@dataclass(frozen=True)
class ReviewResult:
    decision: ReviewDecision
    findings: tuple[Finding, ...]


@dataclass(frozen=True)
class ApprovalRecord:
    review_id: UUID
    status: ApprovalDecision
    reviewer: str
    reason: str

    def __post_init__(self) -> None:
        if self.status not in ("approved", "rejected"):
            raise ValueError("Wrong approval status")
        if not isinstance(self.reviewer, str) or not self.reviewer.strip():
            raise ValueError("Missing reviewer")
        if not isinstance(self.reason, str) or not self.reason.strip():
            raise ValueError("Missing reason")


@dataclass(frozen=True)
class Review:
    review_id: UUID
    result: ReviewResult
    plan_hash: str
    approval_status: ApprovalStatus = "pending"
