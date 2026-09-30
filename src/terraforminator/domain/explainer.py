from terraforminator.domain.models import ReviewResult


def explain_review(review: ReviewResult) -> str:
    explanation = f"The plan was reviewed. Decision: {review.decision}."
    if not review.findings:
        return (
            explanation
            + "\nNo enabled deterministic policy produced a finding. Human approval is still required before deployment."
        )
    explanation += "\nFindings contributing to this decision:\n"
    for finding in review.findings:
        explanation += f"- ID:{finding.id} | severity: {finding.severity} | resource_address: {finding.resource_address} | evidence: {finding.evidence} | remediation: {finding.remediation}\n"
    return explanation
