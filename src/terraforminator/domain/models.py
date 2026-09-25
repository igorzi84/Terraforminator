from dataclasses import dataclass
from typing import Any, Literal

ChangeAction = Literal["create", "update", "delete", "no-op", "read"]
Severity = Literal["low", "medium", "high"]


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
