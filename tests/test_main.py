from datetime import datetime, timedelta
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from terraforminator.deterministic_explanation_provider import (
    DeterministicExplanationProvider,
)
from terraforminator.domain.models import PolicyConfig, ReviewResult
from terraforminator.domain.plan_hash import hash_plan
from terraforminator.main import app, create_app
from terraforminator.review_store import InMemoryReviewStore
from terraforminator.sqlite_review_store import SQLiteReviewStore


class FakeExplanationProvider:
    def explain(self, review: ReviewResult) -> str:
        return "Mocked explanation."


client = TestClient(app)


def test_create_review_approve(create_plan):
    plan_hash = hash_plan(create_plan)
    response = client.post("/reviews", json={"plan": create_plan})
    assert response.status_code == 200
    response_json = response.json()

    assert response_json["decision"] == "approve"
    assert response_json["findings"] == []
    assert "approve" in response_json["explanation"]
    assert "Human approval is still required" in response_json["explanation"]
    assert response_json["plan_hash"] == plan_hash


def test_create_review_block(aws_sg_update_plan):
    finding = {
        "id": "public-inbound-access",
        "severity": "high",
        "resource_address": "aws_security_group.web",
        "evidence": "ingress.cidr_blocks contains 0.0.0.0/0",
        "remediation": "Restrict ingress to approved networks.",
    }
    response = client.post("/reviews", json={"plan": aws_sg_update_plan})
    assert response.status_code == 200

    response_json = response.json()
    assert response_json["decision"] == "block"
    assert response_json["findings"] == [finding]
    assert "explanation" in response_json
    assert finding["id"] in response_json["explanation"]
    assert finding["severity"] in response_json["explanation"]
    assert finding["evidence"] in response_json["explanation"]
    assert finding["resource_address"] in response_json["explanation"]


def test_custom_app_approve(aws_sg_update_plan):
    """We are using custom app with empty policy config, so it shouldnt block anything"""

    custom_app = create_app(
        PolicyConfig(enabled_policy_ids=frozenset()), DeterministicExplanationProvider()
    )
    custom_client = TestClient(custom_app)

    response = custom_client.post("/reviews", json={"plan": aws_sg_update_plan})
    response_json = response.json()
    assert response.status_code == 200
    assert response_json["decision"] == "approve"
    assert response_json["findings"] == []
    assert "approve" in response_json["explanation"]
    assert "Human approval is still required" in response_json["explanation"]


def test_parse_plan_requires_resource_changes():
    response = client.post("/reviews", json={"plan": {}})
    assert response.status_code == 422
    assert response.json() == {
        "detail": {
            "code": "invalid_plan",
            "message": "resource_changes is required",
        }
    }


def test_parse_plan_resource_changes_is_list():
    response = client.post("/reviews", json={"plan": {"resource_changes": {}}})
    assert response.status_code == 422
    assert response.json() == {
        "detail": {
            "code": "invalid_plan",
            "message": "resource_changes must be a list",
        }
    }


def test_parse_plan_item_in_resource_changes_is_dict():
    response = client.post("/reviews", json={"plan": {"resource_changes": [None]}})
    assert response.status_code == 422
    assert response.json() == {
        "detail": {
            "code": "invalid_plan",
            "message": "resource_changes entries must be objects",
        }
    }


def test_parse_plan_resource_changes_change_is_dict():
    response = client.post(
        "/reviews", json={"plan": {"resource_changes": [{"change": None}]}}
    )
    assert response.status_code == 422
    assert response.json() == {
        "detail": {
            "code": "invalid_plan",
            "message": "resource change change field must be an object",
        }
    }


def test_fake_explanation_provider(aws_sg_update_plan):
    custom_app = create_app(
        PolicyConfig(enabled_policy_ids=frozenset({"public-inbound-access"})),
        FakeExplanationProvider(),
    )
    custom_client = TestClient(custom_app)
    finding = {
        "id": "public-inbound-access",
        "severity": "high",
        "resource_address": "aws_security_group.web",
        "evidence": "ingress.cidr_blocks contains 0.0.0.0/0",
        "remediation": "Restrict ingress to approved networks.",
    }
    response = custom_client.post("/reviews", json={"plan": aws_sg_update_plan})
    assert response.status_code == 200

    response_json = response.json()
    assert response_json["findings"] == [finding]
    assert response_json["decision"] == "block"
    assert response_json["explanation"] == "Mocked explanation."


def test_unique_review_id(create_plan):
    first_response = client.post("/reviews", json={"plan": create_plan})
    second_response = client.post("/reviews", json={"plan": create_plan})

    assert first_response.status_code == 200
    assert second_response.status_code == 200

    first_id = UUID(first_response.json()["review_id"])
    second_id = UUID(second_response.json()["review_id"])

    assert first_id.version == 4
    assert second_id.version == 4
    assert first_id != second_id


def test_get_saved_review(aws_sg_update_plan):
    plan_hash = hash_plan(aws_sg_update_plan)
    finding = {
        "id": "public-inbound-access",
        "severity": "high",
        "resource_address": "aws_security_group.web",
        "evidence": "ingress.cidr_blocks contains 0.0.0.0/0",
        "remediation": "Restrict ingress to approved networks.",
    }

    response = client.post("/reviews", json={"plan": aws_sg_update_plan})
    assert response.status_code == 200

    review = response.json()
    review_id = review["review_id"]
    assert review["plan_hash"] == plan_hash

    response = client.get(f"/reviews/{review_id}")
    assert response.status_code == 200

    review = response.json()
    assert review["review_id"] == review_id
    assert review["findings"] == [finding]
    assert review["decision"] == "block"
    assert review["approval_status"] == "pending"
    assert review["plan_hash"] == plan_hash


def test_get_unknown_uuid():
    review_id = uuid4()
    response = client.get(f"/reviews/{review_id}")
    assert response.status_code == 404
    assert response.json() == {
        "detail": {
            "code": "review_not_found",
            "message": "Review not found",
        }
    }


@pytest.mark.parametrize("status", ["approved", "rejected"])
def test_record_human_decision(aws_sg_update_plan, status):
    finding = {
        "id": "public-inbound-access",
        "severity": "high",
        "resource_address": "aws_security_group.web",
        "evidence": "ingress.cidr_blocks contains 0.0.0.0/0",
        "remediation": "Restrict ingress to approved networks.",
    }
    response = client.post("/reviews", json={"plan": aws_sg_update_plan})
    assert response.status_code == 200
    review_id = response.json()["review_id"]

    response = client.post(
        f"/reviews/{review_id}/approval",
        json={"status": status, "reviewer": "Igor", "reason": "Reason"},
    )
    assert response.status_code == 200

    review = response.json()
    assert review["review_id"] == review_id
    assert review["findings"] == [finding]
    assert review["decision"] == "block"
    assert review["approval_status"] == status

    # Verify update persisted in memory
    response = client.get(f"/reviews/{review_id}")
    assert response.status_code == 200

    review = response.json()
    assert review["review_id"] == review_id
    assert review["findings"] == [finding]
    assert review["decision"] == "block"
    assert review["approval_status"] == status


def test_duplicate_approve_review(aws_sg_update_plan):
    finding = {
        "id": "public-inbound-access",
        "severity": "high",
        "resource_address": "aws_security_group.web",
        "evidence": "ingress.cidr_blocks contains 0.0.0.0/0",
        "remediation": "Restrict ingress to approved networks.",
    }

    # Create a review
    response = client.post("/reviews", json={"plan": aws_sg_update_plan})
    assert response.status_code == 200
    review_id = response.json()["review_id"]

    # Approve it
    response = client.post(
        f"/reviews/{review_id}/approval",
        json={"status": "approved", "reviewer": "Igor", "reason": "Reason"},
    )
    assert response.status_code == 200

    review = response.json()
    assert review["review_id"] == review_id
    assert review["findings"] == [finding]
    assert review["decision"] == "block"
    assert review["approval_status"] == "approved"

    # Try to approve again with different status
    response = client.post(
        f"/reviews/{review_id}/approval",
        json={"status": "rejected", "reviewer": "Igor", "reason": "Reason"},
    )
    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "review_not_pending"

    # Get the review and verify it didnt change
    response = client.get(f"/reviews/{review_id}")
    assert response.status_code == 200

    review = response.json()
    assert review["review_id"] == review_id
    assert review["findings"] == [finding]
    assert review["decision"] == "block"
    assert review["approval_status"] == "approved"


def test_approval_with_unknown_uuid():
    review_id = uuid4()
    response = client.post(
        f"/reviews/{review_id}/approval",
        json={"status": "rejected", "reviewer": "Igor", "reason": "Reason"},
    )
    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "review_not_found"


@pytest.mark.parametrize(
    "status, reviewer, reason, error_type, field",
    [
        ("pending", "Igor", "Reason", "literal_error", "status"),
        ("approved", "", "Reason", "value_error", "reviewer"),
        ("approved", "   ", "Reason", "value_error", "reviewer"),
        ("approved", "Igor", "", "value_error", "reason"),
        ("approved", "Igor", "   ", "value_error", "reason"),
    ],
)
def test_invalid_approval_input(
    aws_sg_update_plan, status, reviewer, reason, error_type, field
):
    """
    1. Verifies "pending" is rejected
    2. Verifies error on empty reviewer
    3. Verifies whitespace only reviewer
    4. Verifies error on empty reason
    5. Verifies whitespace only reason
    """
    response = client.post("/reviews", json={"plan": aws_sg_update_plan})
    assert response.status_code == 200
    review_id = response.json()["review_id"]
    response = client.post(
        f"/reviews/{review_id}/approval",
        json={"status": status, "reviewer": reviewer, "reason": reason},
    )
    assert response.status_code == 422

    detail = response.json()["detail"][0]
    assert detail["type"] == error_type
    assert detail["loc"] == ["body", field]


def test_get_approval_record(aws_sg_update_plan):
    response = client.post("/reviews", json={"plan": aws_sg_update_plan})
    assert response.status_code == 200
    review_id = response.json()["review_id"]

    response = client.post(
        f"/reviews/{review_id}/approval",
        json={"status": "approved", "reviewer": "Igor", "reason": "Reason"},
    )
    assert response.status_code == 200

    review = response.json()
    assert review["review_id"] == review_id
    assert review["decision"] == "block"
    assert review["approval_status"] == "approved"

    response = client.get(f"/reviews/{review_id}/approval")
    assert response.status_code == 200

    record = response.json()
    assert record["review_id"] == review_id
    assert record["status"] == "approved"
    assert record["reviewer"] == "Igor"
    assert record["reason"] == "Reason"

    # Verify UTC offset ia zero
    decided_at = datetime.fromisoformat(record["decided_at"])
    assert decided_at.utcoffset() == timedelta(0)

    # Get again
    response = client.get(f"/reviews/{review_id}/approval")
    assert response.status_code == 200

    record = response.json()
    assert datetime.fromisoformat(record["decided_at"]) == decided_at


def test_get_approval_record_for_pending_review(aws_sg_update_plan):
    response = client.post("/reviews", json={"plan": aws_sg_update_plan})
    assert response.status_code == 200
    review_id = response.json()["review_id"]

    response = client.get(f"/reviews/{review_id}/approval")
    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "approval_not_found"


def test_pending_review_can_deploy_false(aws_sg_update_plan):
    """Test that a pending review returns can_deploy = False"""
    response = client.post("/reviews", json={"plan": aws_sg_update_plan})
    assert response.status_code == 200
    review_id = response.json()["review_id"]

    response = client.get(f"/reviews/{review_id}")
    assert response.status_code == 200
    assert response.json()["can_deploy"] is False


def test_blocked_review_can_deploy_false(aws_sg_update_plan):
    """Test blocked review can_deploy = False even if approved by human"""
    response = client.post("/reviews", json={"plan": aws_sg_update_plan})
    assert response.status_code == 200
    review_id = response.json()["review_id"]

    # Approve review
    response = client.post(
        f"/reviews/{review_id}/approval",
        json={"status": "approved", "reviewer": "Igor", "reason": "Reason"},
    )
    assert response.status_code == 200
    assert response.json()["can_deploy"] is False


def test_approved_review_can_deploy(create_plan):
    """Test approved review can_deploy = True"""
    response = client.post("/reviews", json={"plan": create_plan})
    assert response.status_code == 200
    review_id = response.json()["review_id"]

    # Get review before human approval, can_deploy should be False
    response = client.get(f"/reviews/{review_id}")
    assert response.status_code == 200
    assert response.json()["can_deploy"] is False

    # Approve review
    response = client.post(
        f"/reviews/{review_id}/approval",
        json={"status": "approved", "reviewer": "Igor", "reason": "Reason"},
    )
    assert response.status_code == 200
    assert response.json()["can_deploy"] is True

    response = client.get(f"/reviews/{review_id}")
    assert response.status_code == 200
    assert response.json()["can_deploy"] is True


def test_supplied_store(create_plan):
    review_store = InMemoryReviewStore()
    custom_app = create_app(
        PolicyConfig(enabled_policy_ids=frozenset()),
        DeterministicExplanationProvider(),
        review_store,
    )
    custom_client = TestClient(custom_app)

    response = custom_client.post("/reviews", json={"plan": create_plan})
    assert response.status_code == 200
    review_id = response.json()["review_id"]

    stored_review = review_store.get_review(UUID(review_id))
    assert stored_review.review_id == UUID(review_id)
    assert stored_review.plan_hash == hash_plan(create_plan)


def test_sqlite_database(tmp_path, create_plan):
    database_file = tmp_path / "reviews.db"
    review_store = SQLiteReviewStore(database_file)
    custom_app = create_app(
        PolicyConfig(enabled_policy_ids=frozenset()),
        DeterministicExplanationProvider(),
        review_store,
    )
    custom_client = TestClient(custom_app)

    response = custom_client.post("/reviews", json={"plan": create_plan})
    assert response.status_code == 200
    review_id = response.json()["review_id"]

    response = custom_client.post(
        f"/reviews/{review_id}/approval",
        json={"status": "approved", "reviewer": "Igor", "reason": "reason"},
    )
    assert response.status_code == 200
    expected_review = response.json()

    response = custom_client.get(f"/reviews/{review_id}/approval")
    assert response.status_code == 200
    expected_record = response.json()
    
    reopened_store = SQLiteReviewStore(database_file)
    reopened_app = create_app(
        PolicyConfig(enabled_policy_ids=frozenset()),
        DeterministicExplanationProvider(),
        reopened_store,
    )
    reopened_client = TestClient(reopened_app)

    reopened_record = reopened_client.get(f"/reviews/{review_id}/approval")
    assert reopened_record.status_code == 200
    assert reopened_record.json() == expected_record

    reopened_review = reopened_client.get(f"/reviews/{review_id}")
    assert reopened_review.status_code == 200
    assert reopened_review.json() == expected_review
