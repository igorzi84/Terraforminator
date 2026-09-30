from terraforminator.domain.explainer import explain_review
from terraforminator.domain.models import ReviewResult


class DeterministicExplanationProvider:
    def explain(self, review: ReviewResult) -> str:
        return explain_review(review)
