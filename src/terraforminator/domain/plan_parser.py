from terraforminator.domain.errors import InvalidPlanError
from terraforminator.domain.models import ResourceChange


def parse_plan(plan: dict) -> list[ResourceChange]:
    changes = []

    if "resource_changes" not in plan:
        raise InvalidPlanError("resource_changes is required")

    if not isinstance(plan["resource_changes"], list):
        raise InvalidPlanError("resource_changes must be a list")

    for resource_change in plan["resource_changes"]:
        if not isinstance(resource_change, dict):
            raise InvalidPlanError("resource_changes entries must be objects")

        try:
            change = resource_change["change"]
            if not isinstance(change, dict):
                raise InvalidPlanError("resource change change field must be an object")

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
        except KeyError as error:
            raise InvalidPlanError(
                f"resource change is missing a required field: {error.args[0]}"
            ) from error

    return changes
