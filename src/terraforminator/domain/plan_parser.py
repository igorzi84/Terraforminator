from terraforminator.domain.errors import InvalidPlanError
from terraforminator.domain.models import ResourceChange


def parse_plan(plan: dict) -> list[ResourceChange]:
    changes = []

    if "resource_changes" not in plan:
        raise InvalidPlanError("resource_changes is required")

    for resource_change in plan["resource_changes"]:
        change = resource_change["change"]
        normalized_change = ResourceChange(
            address=resource_change["address"],
            resource_type=resource_change["type"],
            name=resource_change["name"],
            actions=tuple(change["actions"]),
            before=change["before"],
            after=change["after"],
            after_unknown=change.get("after_unknown"),
        )
        changes.append(normalized_change)

    return changes
