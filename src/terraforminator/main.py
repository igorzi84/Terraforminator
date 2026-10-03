from pathlib import Path
from uuid import UUID, uuid4

from fastapi import FastAPI, HTTPException

from terraforminator.api.v1.schemas import (
    FindingResponse,
    ReviewRequest,
    ReviewResponse,
    StoredReviewResponse,
)
from terraforminator.config import load_policy_config
from terraforminator.deterministic_explanation_provider import (
    DeterministicExplanationProvider,
)
from terraforminator.domain.errors import InvalidPlanError
from terraforminator.domain.models import PolicyConfig, Review
from terraforminator.domain.plan_parser import parse_plan
from terraforminator.domain.review import evaluate_review
from terraforminator.explanation_provider import ExplanationProvider
from terraforminator.review_store import InMemoryReviewStore

CONFIG_DIR = Path(__file__).parent.parent.parent / "config"
POLICY_CONFIG_PATH = CONFIG_DIR / "policies.toml"


def create_app(
    policy_config: PolicyConfig, explanation_provider: ExplanationProvider
) -> FastAPI:
    app = FastAPI()
    review_store = InMemoryReviewStore()

    @app.post("/reviews")
    def create_review(request: ReviewRequest) -> ReviewResponse:
        review_id = uuid4()

        try:
            changes = parse_plan(request.plan)
        except InvalidPlanError as error:
            raise HTTPException(
                422, detail={"code": "invalid_plan", "message": str(error)}
            )

        result = evaluate_review(changes, policy_config)
        review = Review(review_id=review_id, result=result)
        review_store.save_review(review)

        findings = [
            FindingResponse(
                id=finding.id,
                severity=finding.severity,
                resource_address=finding.resource_address,
                evidence=finding.evidence,
                remediation=finding.remediation,
            )
            for finding in result.findings
        ]
        explanation = explanation_provider.explain(result)

        return ReviewResponse(
            review_id=review_id,
            decision=result.decision,
            findings=findings,
            explanation=explanation,
        )

    @app.get("/reviews/{review_id}")
    def get_review(review_id: UUID) -> StoredReviewResponse:
        try:
            review = review_store.get_review(review_id)
        except KeyError:
            raise HTTPException(
                404, detail={"code": "review_not_found", "message": "Review not found"}
            )

        findings = [
            FindingResponse(
                id=finding.id,
                severity=finding.severity,
                resource_address=finding.resource_address,
                evidence=finding.evidence,
                remediation=finding.remediation,
            )
            for finding in review.result.findings
        ]

        return StoredReviewResponse(
            review_id=review_id,
            decision=review.result.decision,
            findings=findings,
            approval_status=review.approval_status,
        )

    return app


policy_config = load_policy_config(POLICY_CONFIG_PATH)
app = create_app(policy_config, DeterministicExplanationProvider())
