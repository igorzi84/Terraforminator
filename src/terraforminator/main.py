from pathlib import Path

from fastapi import FastAPI, HTTPException

from terraforminator.api.v1.schemas import (
    FindingResponse,
    ReviewRequest,
    ReviewResponse,
)
from terraforminator.config import load_policy_config
from terraforminator.domain.errors import InvalidPlanError
from terraforminator.domain.explainer import explain_review
from terraforminator.domain.models import PolicyConfig
from terraforminator.domain.plan_parser import parse_plan
from terraforminator.domain.review import evaluate_review

CONFIG_DIR = Path(__file__).parent.parent.parent / "config"
POLICY_CONFIG_PATH = CONFIG_DIR / "policies.toml"


def create_app(policy_config: PolicyConfig) -> FastAPI:
    app = FastAPI()

    @app.post("/reviews")
    def create_review(request: ReviewRequest) -> ReviewResponse:
        try:
            changes = parse_plan(request.plan)
        except InvalidPlanError as error:
            raise HTTPException(
                422, detail={"code": "invalid_plan", "message": str(error)}
            )

        review = evaluate_review(changes, policy_config)
        findings = [
            FindingResponse(
                id=finding.id,
                severity=finding.severity,
                resource_address=finding.resource_address,
                evidence=finding.evidence,
                remediation=finding.remediation,
            )
            for finding in review.findings
        ]
        explanation = explain_review(review)

        return ReviewResponse(
            decision=review.decision, findings=findings, explanation=explanation
        )

    return app


policy_config = load_policy_config(POLICY_CONFIG_PATH)
app = create_app(policy_config)
