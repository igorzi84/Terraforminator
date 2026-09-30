from terraforminator.domain.models import Finding, PolicyConfig
from terraforminator.domain.plan_parser import parse_plan
from terraforminator.domain.review import evaluate_review


def test_review_pipeline(aws_sg_update_plan):
    changes = parse_plan(aws_sg_update_plan)
    result = evaluate_review(changes)
    assert result.decision == "block"
    assert result.findings == (
        Finding(
            id="public-inbound-access",
            severity="high",
            resource_address="aws_security_group.web",
            evidence="ingress.cidr_blocks contains 0.0.0.0/0",
            remediation="Restrict ingress to approved networks.",
        ),
    )


def test_review_pipeline_custom_policy(aws_sg_update_plan):
    policy_config = PolicyConfig(enabled_policy_ids=frozenset())
    changes = parse_plan(aws_sg_update_plan)
    result = evaluate_review(changes, policy_config)
    assert result.decision == "approve"
    assert result.findings == ()
