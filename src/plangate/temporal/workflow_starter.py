from typing import Protocol

from temporalio.client import Client

from plangate.domain.models import ApprovalRecord
from plangate.temporal.workflows.approval import ApprovalWorkflow
from plangate.temporal.workflows.models import ApprovalWorkflowInput


class ApprovalWorkflowStarter(Protocol):
    async def start(self, input: ApprovalWorkflowInput) -> str: ...

    async def record_decision(self, approval_record: ApprovalRecord) -> None: ...


class TemporalApprovalWorkflowStarter:
    def __init__(self, client: Client):
        self.client = client

    async def start(self, input: ApprovalWorkflowInput) -> str:
        handle = await self.client.start_workflow(
            ApprovalWorkflow.run,
            input,
            id=f"approval-{input.review_id}",
            task_queue="plangate-approval",
        )
        return handle.id

    async def record_decision(self, approval_record: ApprovalRecord) -> None:
        handle = self.client.get_workflow_handle(
            f"approval-{approval_record.review_id}"
        )
        await handle.signal(ApprovalWorkflow.record_decision, approval_record)
