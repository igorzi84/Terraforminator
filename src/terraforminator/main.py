from pathlib import Path
from uuid import UUID, uuid4

from fastapi import FastAPI, HTTPException

from terraforminator.api.v1.schemas import (
    ApprovalRecordResponse,
    ApprovalRequest,
    FindingResponse,
    ReviewRequest,
    ReviewResponse,
    StoredReviewResponse,
)
from terraforminator.config import load_policy_config
from terraforminator.deterministic_explanation_provider import (
    DeterministicExplanationProvider,
)
from terraforminator.domain.deployment import can_deploy
from terraforminator.domain.errors import InvalidPlanError
from terraforminator.domain.models import ApprovalRecord, PolicyConfig, Review
from terraforminator.domain.plan_hash import hash_plan
from terraforminator.domain.plan_parser import parse_plan
from terraforminator.domain.review import evaluate_review
from terraforminator.explanation_provider import ExplanationProvider
from terraforminator.review_store import InMemoryReviewStore

CONFIG_DIR = Path(__file__).parent.parent.parent / "config"
POLICY_CONFIG_PATH = CONFIG_DIR / "policies.toml"


def to_stored_review_response(review: Review) -> StoredReviewResponse:
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
    deploy = can_deploy(review)
    return StoredReviewResponse(
        review_id=review.review_id,
        plan_hash=review.plan_hash,
        decision=review.result.decision,
        findings=findings,
        approval_status=review.approval_status,
        can_deploy=deploy,
    )


def create_app(
    policy_config: PolicyConfig, explanation_provider: ExplanationProvider
) -> FastAPI:
    app = FastAPI()
    review_store = InMemoryReviewStore()

    @app.post("/reviews")
    def create_review(request: ReviewRequest) -> ReviewResponse:
        review_id = uuid4()
        plan_hash = hash_plan(request.plan)

        try:
            changes = parse_plan(request.plan)
        except InvalidPlanError as error:
            raise HTTPException(
                422, detail={"code": "invalid_plan", "message": str(error)}
            )

        result = evaluate_review(changes, policy_config)
        review = Review(review_id=review_id, result=result, plan_hash=plan_hash)
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
            plan_hash=plan_hash,
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

        return to_stored_review_response(review)

    @app.post("/reviews/{review_id}/approval")
    def approve_review(
        approval_request: ApprovalRequest, review_id: UUID
    ) -> StoredReviewResponse:
        approval_record = ApprovalRecord(
            review_id=review_id,
            status=approval_request.status,
            reviewer=approval_request.reviewer,
            reason=approval_request.reason,
        )
        try:
            review_store.save_approval(approval_record)
        except KeyError:
            raise HTTPException(
                404, detail={"code": "review_not_found", "message": "Review not found"}
            )
        except ValueError:
            raise HTTPException(
                409,
                detail={
                    "code": "review_not_pending",
                    "message": "Review already has a human decision",
                },
            )

        review = review_store.get_review(review_id=review_id)
        return to_stored_review_response(review)

    @app.get("/reviews/{review_id}/approval")
    def get_record(review_id: UUID) -> ApprovalRecordResponse:
        try:
            record = review_store.get_record(review_id)
        except KeyError:
            raise HTTPException(
                404,
                detail={
                    "code": "approval_not_found",
                    "message": "Approval record not found.",
                },
            )

        return ApprovalRecordResponse(
            review_id=review_id,
            status=record.status,
            reviewer=record.reviewer,
            reason=record.reason,
        )

    return app


policy_config = load_policy_config(POLICY_CONFIG_PATH)
app = create_app(policy_config, DeterministicExplanationProvider())
