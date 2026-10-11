from typing import Protocol

from terraforminator.domain.models import ReviewResult


class ExplanationProvider(Protocol):
    name: str

    def explain(self, review: ReviewResult) -> str: ...
