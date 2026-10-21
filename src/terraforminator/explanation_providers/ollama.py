import httpx2

from terraforminator.domain.models import ReviewResult


class OllamaExplanationProvider:
    name = "ollama"

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
        response = httpx2.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "qwen3:4b",
                "prompt": prompt,
                "stream": False,
            },
            timeout=120.0,
        )
        response.raise_for_status()
        return response.json()["response"]
