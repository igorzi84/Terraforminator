from terraforminator.domain.models import ResourceChange
from terraforminator.domain.policies import evaluate_policies


def test_evaluate_policies_returns_no_findings_for_no_changes():
    assert evaluate_policies([]) == []


def test_evaluate_policies_public_inbound_access():
    change = ResourceChange(
        address="aws_security_group.web",
        resource_type="aws_security_group",
        name="web",
        actions=("create",),
        before=None,
        after={
            "ingress": [
                {
                    "cidr_blocks": ["0.0.0.0/0"],
                    "from_port": 443,
                    "to_port": 443,
                    "protocol": "tcp",
                }
            ]
        },
    )

    findings = evaluate_policies([change])

    assert len(findings) == 1

    finding = findings[0]
    assert finding.id == "public-inbound-access"
    assert finding.severity == "high"
    assert finding.resource_address == "aws_security_group.web"


def test_evaluate_policies_ignores_private_inbound_access():
    change = ResourceChange(
        address="aws_security_group.web",
        resource_type="aws_security_group",
        name="web",
        actions=("create",),
        before=None,
        after={
            "ingress": [
                {
                    "cidr_blocks": ["10.0.0.0/16"],
                    "from_port": 443,
                    "to_port": 443,
                    "protocol": "tcp",
                }
            ]
        },
    )

    assert evaluate_policies([change]) == []
