from terraforminator.domain.models import Finding, PolicyConfig, ResourceChange


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


def test_finding_keeps_policy_details():
    finding = Finding(
        id="public-inbound-access",
        severity="high",
        resource_address="aws_security_group.web",
        evidence="ingress.cidr_blocks contains 0.0.0.0/0",
        remediation="Restrict ingress to approved networks.",
    )

    assert finding.severity == "high"
    assert finding.resource_address == "aws_security_group.web"


def test_policy_config_subset():
    policy_config = PolicyConfig(
        enabled_policy_ids=frozenset({"public-inbound-access"})
    )

    assert "public-inbound-access" in policy_config.enabled_policy_ids
    assert "iam-wildcard-permission" not in policy_config.enabled_policy_ids
