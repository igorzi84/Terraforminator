from prometheus_client import CollectorRegistry, Counter, Histogram

from terraforminator.domain.models import ApprovalDecision, ReviewDecision


class ReviewMetrics:
    def __init__(self) -> None:
        self.registry = CollectorRegistry()

        self.reviews_total = Counter(
            "terraforminator_reviews_total",
            "Total successfully completed reviews",
            labelnames=("policy_result",),
            registry=self.registry,
        )

        self.approvals_total = Counter(
            "terraforminator_approval_decisions_total",
            "Total successfully recorded human decisions",
            labelnames=("approval_outcome",),
            registry=self.registry,
        )

        self.review_duration = Histogram(
            "terraforminator_review_duration_seconds",
            "Review duration",
            labelnames=("policy_result",),
            registry=self.registry,
        )

    def record_review(self, policy_result: ReviewDecision) -> None:
        self.reviews_total.labels(policy_result=policy_result).inc()

    def record_approval(self, approval_outcome: ApprovalDecision) -> None:
        self.approvals_total.labels(approval_outcome=approval_outcome).inc()

    def record_review_duration(
        self, policy_result: ReviewDecision, seconds: float
    ) -> None:
        self.review_duration.labels(policy_result=policy_result).observe(seconds)
