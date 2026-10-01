from uuid import UUID

from fastapi.testclient import TestClient

from terraforminator.deterministic_explanation_provider import (
    DeterministicExplanationProvider,
)
from terraforminator.domain.models import PolicyConfig, ReviewResult
from terraforminator.main import app, create_app


class FakeExplanationProvider:
    def explain(self, review: ReviewResult) -> str:
        return "Mocked explanation."


client = TestClient(app)


def test_create_review_approve(create_plan):
    response = client.post("/reviews", json={"plan": create_plan})
    assert response.status_code == 200
    response_json = response.json()

    assert response_json["decision"] == "approve"
    assert response_json["findings"] == []
    assert "approve" in response_json["explanation"]
    assert "Human approval is still required" in response_json["explanation"]


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
