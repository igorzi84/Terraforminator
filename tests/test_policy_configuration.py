from pathlib import Path

from terraforminator.config import load_policy_config
from terraforminator.domain.models import ResourceChange
from terraforminator.domain.policies import evaluate_policies

CONFIG_DIR = Path(__file__).parent / "fixtures" / "config"


def test_policy_configuration():
    config_path = CONFIG_DIR / "public-inbound-only.toml"
    policy_config = load_policy_config(config_path)
    changes = [
        ResourceChange(
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
        ),
        ResourceChange(
            address="aws_iam_policy.app",
            resource_type="aws_iam_policy",
            name="app",
            actions=("create",),
            before=None,
            after={
                "name": "app-policy",
                "path": "/",
                "policy": '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Action":"*","Resource":"*"}]}',
                "tags": None,
            },
        ),
    ]

    findings = evaluate_policies(changes, policy_config)
    assert len(findings) == 1

    finding = findings[0]

    assert finding.id == "public-inbound-access"
    assert finding.severity == "high"
    assert finding.resource_address == "aws_security_group.web"
    assert finding.evidence == "ingress.cidr_blocks contains 0.0.0.0/0"
    assert finding.remediation == "Restrict ingress to approved networks."
