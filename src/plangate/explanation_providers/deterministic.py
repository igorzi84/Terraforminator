from plangate.domain.explainer import explain_review
from plangate.domain.models import ReviewResult


class DeterministicExplanationProvider:
    name = "deterministic"

    def explain(self, review: ReviewResult) -> str:
        return explain_review(review)
