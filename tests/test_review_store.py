from uuid import uuid4

import pytest

from terraforminator.domain.models import Review, ReviewResult
from terraforminator.review_store import InMemoryReviewStore


def test_save_and_retrieve_review():
    store = InMemoryReviewStore()
    review_id = uuid4()
    review = Review(
        review_id=review_id,
        result=ReviewResult(decision="approve", findings=()),
    )
    store.save_review(review)
    retrieved_review = store.get_review(review_id)
    assert retrieved_review == review


def test_stores_isolation():
    first_store = InMemoryReviewStore()
    second_store = InMemoryReviewStore()
    review_id = uuid4()
    review = Review(
        review_id=review_id,
        result=ReviewResult(decision="approve", findings=()),
    )
    first_store.save_review(review)
    with pytest.raises(KeyError):
        second_store.get_review(review_id)
