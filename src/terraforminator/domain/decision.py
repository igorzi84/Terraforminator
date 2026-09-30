from terraforminator.domain.models import Finding, ReviewDecision


def decide_review(findings: list[Finding]) -> ReviewDecision:
    if any(finding.severity == "high" for finding in findings):
        return "block"
    if any(finding.severity == "medium" for finding in findings):
        return "needs_review"

    return "approve"
