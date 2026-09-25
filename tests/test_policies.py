import json

import pytest

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
    assert finding.evidence == "ingress.cidr_blocks contains 0.0.0.0/0"
    assert finding.remediation == "Restrict ingress to approved networks."


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


def test_evaluate_policies_noop_public_inbound_access():
    change = ResourceChange(
        address="aws_security_group.web",
        resource_type="aws_security_group",
        name="web",
        actions=("no-op",),
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
    assert evaluate_policies([change]) == []


def test_evaluate_policies_iam_no_wildcard():
    change = ResourceChange(
        address="aws_iam_policy.app",
        resource_type="aws_iam_policy",
        name="app",
        actions=("create",),
        before=None,
        after={
            "name": "app-policy",
            "path": "/",
            "policy": '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Action":"s3:GetObject","Resource":"arn:aws:s3:::terraforminator-demo/*"}]}',
            "tags": None,
        },
    )
    assert evaluate_policies([change]) == []


@pytest.mark.parametrize(
    ("action", "resource"),
    [
        ("*", "*"),
        ("*", "arn:aws:s3:::terraforminator-demo/*"),
        ("s3:GetObject", "*"),
    ],
)
def test_evaluate_policies_iam_wildcard(action, resource):
    change = ResourceChange(
        address="aws_iam_policy.app",
        resource_type="aws_iam_policy",
        name="app",
        actions=("create",),
        before=None,
        after={
            "name": "app-policy",
            "path": "/",
            "policy": json.dumps(
                {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Action": action,
                            "Resource": resource,
                        }
                    ],
                },
            ),
            "tags": None,
        },
    )

    findings = evaluate_policies([change])
    assert len(findings) == 1

    finding = findings[0]
    assert finding.id == "iam-wildcard-permission"
    assert finding.severity == "high"
    assert finding.resource_address == "aws_iam_policy.app"
    assert finding.evidence == "policy.statement contains wildcard permissions"
    assert (
        finding.remediation
        == "Replace wildcard actions and resources with the minimum required permissions."
    )


def test_evaluate_policies_iam_wildcard_deny():
    change = ResourceChange(
        address="aws_iam_policy.app",
        resource_type="aws_iam_policy",
        name="app",
        actions=("create",),
        before=None,
        after={
            "name": "app-policy",
            "path": "/",
            "policy": '{"Version":"2012-10-17","Statement":[{"Effect":"Deny","Action":"*","Resource":"*"}]}',
            "tags": None,
        },
    )
    assert evaluate_policies([change]) == []
