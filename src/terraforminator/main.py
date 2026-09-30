from fastapi import FastAPI

from terraforminator.api.v1.schemas import (
    FindingResponse,
    ReviewRequest,
    ReviewResponse,
)
from terraforminator.domain.plan_parser import parse_plan
from terraforminator.domain.review import evaluate_review

app = FastAPI()


@app.post("/reviews")
def create_review(request: ReviewRequest) -> ReviewResponse:
    changes = parse_plan(request.plan)
    review = evaluate_review(changes)
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

    return ReviewResponse(decision=review.decision, findings=findings)
