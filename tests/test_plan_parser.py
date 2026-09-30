import pytest

from terraforminator.domain.errors import InvalidPlanError
from terraforminator.domain.plan_parser import parse_plan


def test_parse_plan_create(create_plan):
    parsed_plan = parse_plan(create_plan)
    assert len(parsed_plan) == 2

    # Compare changes by address
    actions_by_address = {change.address: change.actions for change in parsed_plan}

    assert actions_by_address == {
        "docker_container.nginx": ("create",),
        "docker_image.nginx": ("create",),
    }

    container = next(
        change for change in parsed_plan if change.address == "docker_container.nginx"
    )
    assert container.after_unknown is not None
    assert container.after_unknown["id"] is True


def test_parse_plan_noop(noop_plan):
    parsed_plan = parse_plan(noop_plan)
    assert len(parsed_plan) == 2

    # Compare changes by address
    actions_by_address = {change.address: change.actions for change in parsed_plan}

    assert actions_by_address == {
        "docker_container.nginx": ("no-op",),
        "docker_image.nginx": ("no-op",),
    }


def test_parse_plan_requires_resource_changes():
    with pytest.raises(InvalidPlanError, match="resource_changes is required"):
        parse_plan({})


def test_parse_plan_resource_changes_is_list():
    with pytest.raises(InvalidPlanError, match="resource_changes must be a list"):
        parse_plan({"resource_changes": {}})


def test_parse_plan_item_in_resource_changes_is_dict():
    with pytest.raises(
        InvalidPlanError, match="resource_changes entries must be objects"
    ):
        parse_plan({"resource_changes": [None]})


def test_parse_plan_change_missing_required_field():
    with pytest.raises(
        InvalidPlanError, match="resource change is missing a required field: change"
    ):
        parse_plan({"resource_changes": [{}]})


def test_parse_plan_resource_changes_change_is_dict():
    with pytest.raises(
        InvalidPlanError, match="resource change change field must be an object"
    ):
        parse_plan({"resource_changes": [{"change": None}]})
