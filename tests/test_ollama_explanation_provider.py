from unittest.mock import Mock

import pytest
from pydantic import AnyUrl

from terraforminator.config import AppSettings
from terraforminator.domain.models import ReviewResult
from terraforminator.explanation_providers import ollama

TEST_SETTINGS = AppSettings(
    llm_provider="ollama",
    ollama_url=AnyUrl("http://ollama.test:11434"),
    llm_model="test-model",
    llm_timeout=15,
)


def test_explain(monkeypatch):
    response = Mock()
    response.json.return_value = {"response": "Test explanation"}

    post = Mock(return_value=response)
    monkeypatch.setattr(ollama.httpx2, "post", post)

    review = ReviewResult(decision="approve", findings=())

    provider = ollama.OllamaExplanationProvider(TEST_SETTINGS)
    result = provider.explain(review)

    assert result == "Test explanation"
    response.raise_for_status.assert_called_once_with()

    post.assert_called_once()
    assert post.call_args.args[0] == "http://ollama.test:11434/api/generate"
    assert post.call_args.kwargs["timeout"] == 15
    payload = post.call_args.kwargs["json"]

    assert payload["model"] == "test-model"
    assert payload["stream"] is False
    assert review.decision in payload["prompt"]


def test_explain_propagates_error(monkeypatch):
    response = Mock()
    response.raise_for_status.side_effect = RuntimeError("HTTP error")

    post = Mock(return_value=response)
    monkeypatch.setattr(ollama.httpx2, "post", post)

    review = ReviewResult(decision="approve", findings=())

    provider = ollama.OllamaExplanationProvider(TEST_SETTINGS)
    with pytest.raises(RuntimeError, match="HTTP error"):
        provider.explain(review)

    response.json.assert_not_called()
