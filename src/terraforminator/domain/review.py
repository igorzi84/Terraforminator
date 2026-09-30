from terraforminator.domain.decision import decide_review
from terraforminator.domain.models import PolicyConfig, ReviewResult
from terraforminator.domain.policies import evaluate_policies


def evaluate_review(changes, policy_config: PolicyConfig | None = None) -> ReviewResult:
    findings = evaluate_policies(changes, policy_config)
    decision = decide_review(findings)
    return ReviewResult(decision=decision, findings=tuple(findings))
