from unittest.mock import Mock

import pytest

from terraforminator.domain.models import ReviewResult
from terraforminator.explanation_providers import ollama


def test_explain(monkeypatch):
    response = Mock()
    response.json.return_value = {"response": "Test explanation"}

    post = Mock(return_value=response)
    monkeypatch.setattr(ollama.httpx2, "post", post)

    review = ReviewResult(decision="approve", findings=())

    provider = ollama.OllamaExplanationProvider()
    result = provider.explain(review)

    assert result == "Test explanation"
    response.raise_for_status.assert_called_once_with()

    post.assert_called_once()
    payload = post.call_args.kwargs["json"]

    assert payload["model"] == "qwen3:4b"
    assert payload["stream"] is False
    assert review.decision in payload["prompt"]


def test_explain_propagates_error(monkeypatch):
    response = Mock()
    response.raise_for_status.side_effect = RuntimeError("HTTP error")

    post = Mock(return_value=response)
    monkeypatch.setattr(ollama.httpx2, "post", post)

    review = ReviewResult(decision="approve", findings=())

    provider = ollama.OllamaExplanationProvider()
    with pytest.raises(RuntimeError, match="HTTP error"):
        provider.explain(review)

    response.json.assert_not_called()
