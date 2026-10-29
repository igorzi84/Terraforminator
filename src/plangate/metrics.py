from prometheus_client import CollectorRegistry, Counter, Histogram

from plangate.domain.models import ApprovalDecision, Finding, ReviewDecision


class ReviewMetrics:
    def __init__(self) -> None:
        self.registry = CollectorRegistry()

        self.reviews_total = Counter(
            "plangate_reviews_total",
            "Total successfully completed reviews",
            labelnames=("policy_result",),
            registry=self.registry,
        )

        self.approvals_total = Counter(
            "plangate_approval_submissions_total",
            "Total approval submissions",
            labelnames=("requested_status",),
            registry=self.registry,
        )

        self.review_duration = Histogram(
            "plangate_review_duration_seconds",
            "Review duration",
            labelnames=("policy_result",),
            registry=self.registry,
        )

        self.explanation_duration = Histogram(
            "plangate_explanation_duration_seconds",
            "AI explanation duration",
            labelnames=("provider_name",),
            registry=self.registry,
        )

        self.policy_findings_total = Counter(
            "plangate_policy_findings_total",
            "Total policy findings",
            labelnames=("policy_id", "severity"),
            registry=self.registry,
        )

        self.explanation_fallbacks_total = Counter(
            "plangate_explanation_fallbacks_total",
            "Total fallback events per provider",
            labelnames=("provider_name",),
            registry=self.registry,
        )

    def record_review(self, policy_result: ReviewDecision) -> None:
        self.reviews_total.labels(policy_result=policy_result).inc()

    def record_approval_submission(self, requested_status: ApprovalDecision) -> None:
        self.approvals_total.labels(requested_status=requested_status).inc()

    def record_review_duration(
        self, policy_result: ReviewDecision, seconds: float
    ) -> None:
        self.review_duration.labels(policy_result=policy_result).observe(seconds)

    def record_explanation_duration(self, provider_name: str, seconds: float) -> None:
        self.explanation_duration.labels(provider_name=provider_name).observe(seconds)

    def record_policy_findings(self, finding: Finding) -> None:
        self.policy_findings_total.labels(
            policy_id=finding.id, severity=finding.severity
        ).inc()

    def record_explanation_fallback(self, provider_name: str) -> None:
        self.explanation_fallbacks_total.labels(provider_name=provider_name).inc()
