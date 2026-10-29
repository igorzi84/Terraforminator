import httpx2

from plangate.config import AppSettings
from plangate.domain.models import ReviewResult


class OllamaExplanationProvider:
    name = "ollama"

    def __init__(self, settings: AppSettings) -> None:
        self.settings = settings

    def explain(self, review: ReviewResult) -> str:
        prompt = self.build_prompt(review)
        return self.ask(prompt)

    def build_prompt(self, review: ReviewResult) -> str:
        return f"""
            You explain infrastructure policy findings.

            Use only the supplied evidence. Do not assume ports, protocols,
            attached resources, network reachability, or successful access.
            The policy decision is final. Human approval is still required.
            Write two sentences: explain the finding, then give remediation.

            If there are no findings, say no enabled policy found a violation
            and human approval is still required before deployment.

            Findings - {review.findings}
            Decision - {review.decision}
        """

    def ask(self, prompt: str) -> str:
        base_url = str(self.settings.ollama_url).rstrip("/")
        response = httpx2.post(
            f"{base_url}/api/generate",
            json={
                "model": self.settings.llm_model,
                "prompt": prompt,
                "stream": False,
            },
            timeout=self.settings.llm_timeout,
        )
        response.raise_for_status()
        return response.json()["response"]
