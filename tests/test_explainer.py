from terraforminator.domain.explainer import explain_review
from terraforminator.domain.models import Finding, ReviewResult


def test_blocked_review():
    finding = Finding(
        id="missing-storage-encryption",
        severity="high",
        resource_address="Resource address",
        evidence="after.encrypted is false",
        remediation="Enable encryption for the storage resource.",
    )
    review_result = ReviewResult(
        decision="block",
        findings=(finding,),
    )
    explanation = explain_review(review_result)
    assert "block" in explanation
    assert finding.severity in explanation
    assert finding.id in explanation
    assert finding.resource_address in explanation
    assert finding.evidence in explanation
    assert finding.remediation in explanation


def test_approved_review():
    review_result = ReviewResult(decision="approve", findings=())
    explanation = explain_review(review_result)
    assert "approve" in explanation
    assert "Human approval is still required before deployment" in explanation
