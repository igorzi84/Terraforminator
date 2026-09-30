from fastapi.testclient import TestClient

from terraforminator.domain.models import PolicyConfig
from terraforminator.main import app, create_app

client = TestClient(app)


def test_create_review_approve(create_plan):
    response = client.post("/reviews", json={"plan": create_plan})
    assert response.status_code == 200
    assert response.json() == {"decision": "approve", "findings": []}


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
    assert response.json() == {"decision": "block", "findings": [finding]}


def test_custom_app_approve(aws_sg_update_plan):
    """We are using custom app with empty policy config, so it shouldnt block anything"""

    custom_app = create_app(PolicyConfig(enabled_policy_ids=frozenset()))
    custom_client = TestClient(custom_app)

    response = custom_client.post("/reviews", json={"plan": aws_sg_update_plan})
    assert response.status_code == 200
    assert response.json() == {"decision": "approve", "findings": []}
