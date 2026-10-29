from plangate.domain.decision import decide_review
from plangate.domain.models import PolicyConfig, ReviewResult
from plangate.domain.policies import evaluate_policies


def evaluate_review(changes, policy_config: PolicyConfig | None = None) -> ReviewResult:
    findings = evaluate_policies(changes, policy_config)
    decision = decide_review(findings)
    return ReviewResult(decision=decision, findings=tuple(findings))
