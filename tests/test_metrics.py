from terraforminator.metrics import ReviewMetrics


def test_record_review():
    metrics = ReviewMetrics()
    metrics.record_review("approve")
    metrics.record_review("approve")
    assert (
        metrics.registry.get_sample_value(
            "terraforminator_reviews_total",
            {"policy_result": "approve"},
        )
        == 2
    )


def test_metrics_are_isolated():
    first_metrics = ReviewMetrics()
    second_metrics = ReviewMetrics()

    first_metrics.record_review("approve")
    first_metrics.record_review("approve")
    second_metrics.record_review("approve")

    assert (
        first_metrics.registry.get_sample_value(
            "terraforminator_reviews_total",
            {"policy_result": "approve"},
        )
        == 2
    )

    assert (
        second_metrics.registry.get_sample_value(
            "terraforminator_reviews_total",
            {"policy_result": "approve"},
        )
        == 1
    )
