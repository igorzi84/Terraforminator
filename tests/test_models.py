from terraforminator.domain.models import ResourceChange


def test_replacement_keeps_both_actions():
    rc = ResourceChange(
        address="some_address",
        resource_type="some_rtype",
        name="some_name",
        actions=("delete", "create"),
        before=None,
        after=None,
    )

    assert rc.actions == ("delete", "create")
