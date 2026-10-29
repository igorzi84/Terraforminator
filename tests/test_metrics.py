from plangate.metrics import ReviewMetrics


def test_record_review():
    metrics = ReviewMetrics()
    metrics.record_review("approve")
    metrics.record_review("approve")
    assert (
        metrics.registry.get_sample_value(
            "plangate_reviews_total",
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
            "plangate_reviews_total",
            {"policy_result": "approve"},
        )
        == 2
    )

    assert (
        second_metrics.registry.get_sample_value(
            "plangate_reviews_total",
            {"policy_result": "approve"},
        )
        == 1
    )


def test_record_review_duration():
    metrics = ReviewMetrics()
    metrics.record_review_duration("approve", 0.25)

    assert (
        metrics.registry.get_sample_value(
            "plangate_review_duration_seconds_count",
            {"policy_result": "approve"},
        )
        == 1
    )

    assert (
        metrics.registry.get_sample_value(
            "plangate_review_duration_seconds_sum", {"policy_result": "approve"}
        )
        == 0.25
    )


def test_record_explanation_duration():
    metrics = ReviewMetrics()
    metrics.record_explanation_duration("chatGPT", 0.25)

    assert (
        metrics.registry.get_sample_value(
            "plangate_explanation_duration_seconds_count",
            {"provider_name": "chatGPT"},
        )
        == 1
    )

    assert (
        metrics.registry.get_sample_value(
            "plangate_explanation_duration_seconds_sum", {"provider_name": "chatGPT"}
        )
        == 0.25
    )
