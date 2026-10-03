from uuid import UUID

from terraforminator.domain.models import Review


class InMemoryReviewStore:
    def __init__(self) -> None:
        self.reviews: dict[UUID, Review] = {}

    def get_review(self, review_id: UUID) -> Review:
        return self.reviews[review_id]

    def save_review(self, review: Review) -> None:
        self.reviews[review.review_id] = review
