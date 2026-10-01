from uuid import uuid4

import pytest

from terraforminator.domain.models import (
    ApprovalRecord,
    Finding,
    PolicyConfig,
    ResourceChange,
    ReviewResult,
)


def test_replacement_keeps_both_actions():
    rc = ResourceChange(
        address="some_address",
        resource_type="some_rtype",
        name="some_name",
        actions=("delete", "create"),
        before=None,
        after=None,
    )

    assert rc.actions == ("delete", "create")


def test_finding_keeps_policy_details():
    finding = Finding(
        id="public-inbound-access",
        severity="high",
        resource_address="aws_security_group.web",
        evidence="ingress.cidr_blocks contains 0.0.0.0/0",
        remediation="Restrict ingress to approved networks.",
    )

    assert finding.severity == "high"
    assert finding.resource_address == "aws_security_group.web"


def test_policy_config_subset():
    policy_config = PolicyConfig(
        enabled_policy_ids=frozenset({"public-inbound-access"})
    )

    assert "public-inbound-access" in policy_config.enabled_policy_ids
    assert "iam-wildcard-permission" not in policy_config.enabled_policy_ids


def test_policy_config_required_tags():
    policy_config = PolicyConfig()
    assert policy_config.required_tags == frozenset({"Project", "Environment", "Owner"})


def test_review_result():
    finding = Finding(
        id="public-inbound-access",
        severity="high",
        resource_address="aws_security_group.web",
        evidence="ingress.cidr_blocks contains 0.0.0.0/0",
        remediation="Restrict ingress to approved networks.",
    )
    assert ReviewResult(decision="approve", findings=(finding,))


@pytest.mark.parametrize("status", ["approved", "rejected"])
def test_approval_record(status):
    review_id = uuid4()
    approval_record = ApprovalRecord(
        review_id=review_id, status=status, reviewer="Igor", reason="Reason"
    )
    assert approval_record.review_id == review_id
    assert approval_record.status == status


@pytest.mark.parametrize("status", ["pending", "", None])
def test_approval_record_raises_error_on_wrong_status(status):
    with pytest.raises(ValueError, match="Wrong approval status"):
        ApprovalRecord(
            review_id=uuid4(), status=status, reviewer="Igor", reason="Reason"
        )


@pytest.mark.parametrize("reviewer", ["", " ", None])
def test_approval_record_raises_error_on_missing_reviewer(reviewer):
    with pytest.raises(ValueError, match="Missing reviewer"):
        ApprovalRecord(
            review_id=uuid4(), status="approved", reviewer=reviewer, reason="Reason"
        )


@pytest.mark.parametrize("reason", ["", " ", None])
def test_approval_record_raises_error_on_missing_reason(reason):
    with pytest.raises(ValueError, match="Missing reason"):
        ApprovalRecord(
            review_id=uuid4(), status="approved", reviewer="Igor", reason=reason
        )
