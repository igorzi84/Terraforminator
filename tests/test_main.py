from fastapi.testclient import TestClient

from terraforminator.main import app

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
