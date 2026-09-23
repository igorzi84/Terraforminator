from dataclasses import dataclass
from typing import Any, Literal

ChangeAction = Literal["create", "update", "delete", "no-op", "read"]

@dataclass(frozen=True)
class ResourceChange:
    address: str
    resource_type: str
    name: str
    actions: tuple[ChangeAction, ...]
    before: dict[str, Any] | None
    after: dict[str, Any] | None

