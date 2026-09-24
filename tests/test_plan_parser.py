from terraforminator.domain.plan_parser import parse_plan


def test_parse_plan_create(create_plan):
    parsed_plan = parse_plan(create_plan)
    assert len(parsed_plan) == 2

    # Compare changes by address
    actions_by_address = {
      change.address: change.actions
      for change in parsed_plan
  }

    assert actions_by_address == {
        "docker_container.nginx": ("create",),
        "docker_image.nginx": ("create",),
    }


def test_parse_plan_noop(noop_plan):
    parsed_plan = parse_plan(noop_plan)
    assert len(parsed_plan) == 2

    # Compare changes by address
    actions_by_address = {
        change.address: change.actions
        for change in parsed_plan
    }
    
    assert actions_by_address == {
        "docker_container.nginx": ("no-op",),
        "docker_image.nginx": ("no-op",),
    }