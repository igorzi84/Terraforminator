from dataclasses import dataclass
from typing import Any, Literal

ChangeAction = Literal["create", "update", "delete", "no-op", "read"]
Severity = Literal["low", "medium", "high"]
ReviewDecision = Literal["approve", "needs_review", "block"]

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
            "missing-required-tags"
        }
    )
    required_tags: frozenset[str] = frozenset({"Project", "Environment", "Owner"})
