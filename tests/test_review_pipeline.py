from terraforminator.domain.decision import decide_review
from terraforminator.domain.plan_parser import parse_plan
from terraforminator.domain.policies import evaluate_policies


def test_review_pipeline(aws_sg_update_plan):
    changes = parse_plan(aws_sg_update_plan)
    findings = evaluate_policies(changes)
    assert decide_review(findings) == "block"

