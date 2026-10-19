import asyncio
from concurrent.futures import ThreadPoolExecutor

import pytest
from httpx import ASGITransport, AsyncClient
from temporalio.contrib.pydantic import pydantic_data_converter
from temporalio.testing import WorkflowEnvironment
from temporalio.worker import Worker
from temporalio.worker.workflow_sandbox import (
    SandboxedWorkflowRunner,
    SandboxRestrictions,
)

from terraforminator.config import AppSettings
from terraforminator.deterministic_explanation_provider import (
    DeterministicExplanationProvider,
)
from terraforminator.domain.models import PolicyConfig
from terraforminator.main import create_app
from terraforminator.sqlite_review_store import SQLiteReviewStore
from terraforminator.temporal.activities.approval import ApprovalActivities
from terraforminator.temporal.workflow_starter import TemporalApprovalWorkflowStarter
from terraforminator.temporal.workflows.approval import ApprovalWorkflow


@pytest.mark.parametrize(
    "plan_fixture, expected_decision, can_deploy",
    [
        ("aws_sg_update_plan", "block", False),
        ("create_plan", "approve", True),
    ],
)
def test_temporal_approval(
    tmp_path, request, plan_fixture, expected_decision, can_deploy
):
    plan = request.getfixturevalue(plan_fixture)

    async def run_test():
        async with await WorkflowEnvironment.start_local(
            data_converter=pydantic_data_converter,
        ) as env:
            store = SQLiteReviewStore(tmp_path / "reviews.db")
            activities = ApprovalActivities(store)

            with ThreadPoolExecutor(max_workers=2) as executor:
                async with Worker(
                    env.client,
                    task_queue="terraforminator-approval",
                    workflows=[ApprovalWorkflow],
                    activities=[activities.save_approval],
                    activity_executor=executor,
                    workflow_runner=SandboxedWorkflowRunner(
                        restrictions=SandboxRestrictions.default.with_passthrough_modules(
                            "annotated_types"
                        ),
                    ),
                ):
                    app = create_app(
                        PolicyConfig(),
                        DeterministicExplanationProvider(),
                        settings=AppSettings(
                            database_path=tmp_path / "reviews.db",
                            host="127.0.0.1",
                            temporal_address=env.client.service_client.config.target_host,
                        ),
                        review_store=store,
                        workflow_starter=TemporalApprovalWorkflowStarter(env.client),
                    )

                    async with (
                        app.router.lifespan_context(app),
                        AsyncClient(
                            transport=ASGITransport(app=app),
                            base_url="http://test",
                        ) as client,
                    ):
                        response = await client.post("/reviews", json={"plan": plan})
                        assert response.status_code == 200
                        review_id = response.json()["review_id"]
                        assert response.json()["decision"] == expected_decision

                        response = await client.get(f"/reviews/{review_id}")
                        assert response.status_code == 200
                        assert response.json()["approval_status"] == "pending"

                        response = await client.post(
                            f"/reviews/{review_id}/approval",
                            json={
                                "status": "approved",
                                "reviewer": "Igor",
                                "reason": "Reviewed the plan",
                            },
                        )
                        assert response.status_code == 202

                        handle = env.client.get_workflow_handle(f"approval-{review_id}")
                        result = await asyncio.wait_for(handle.result(), timeout=15)
                        assert result == "approved"

                        response = await client.get(f"/reviews/{review_id}")
                        assert response.status_code == 200
                        assert response.json()["approval_status"] == "approved"
                        assert response.json()["can_deploy"] is can_deploy

                        response = await client.get(f"/reviews/{review_id}/approval")
                        assert response.status_code == 200
                        audit = response.json()
                        assert audit["status"] == "approved"
                        assert audit["reviewer"] == "Igor"
                        assert audit["reason"] == "Reviewed the plan"

    asyncio.run(run_test())
