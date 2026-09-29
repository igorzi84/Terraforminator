from terraforminator.domain.decision import decide_review
from terraforminator.domain.models import Finding

LOW_SEVERITY_FINDING = Finding(
    id="test-approve",
    severity="low",
    resource_address="Resource address",
    evidence="Something low severity",
    remediation="No remediation.",
)

MEDIUM_SEVERITY_FINDING = Finding(
    id="missing-required-tags",
    severity="medium",
    resource_address="Resource address",
    evidence="Missing tags: Owner",
    remediation="Add the required tags before approving the change.",
)

HIGH_SEVERITY_FINDING = Finding(
    id="missing-storage-encryption",
    severity="high",
    resource_address="Resource address",
    evidence="after.encrypted is false",
    remediation="Enable encryption for the storage resource.",
)


def test_decide_review_empty_approve():
    assert decide_review([]) == "approve"


def test_decide_review_approve():
    assert decide_review([LOW_SEVERITY_FINDING]) == "approve"


def test_decide_review_needs_review():
    findings = [LOW_SEVERITY_FINDING, MEDIUM_SEVERITY_FINDING]
    assert decide_review(findings) == "needs_review"


def test_decide_review_block():
    findings = [LOW_SEVERITY_FINDING, MEDIUM_SEVERITY_FINDING, HIGH_SEVERITY_FINDING]
    assert decide_review(findings) == "block"
