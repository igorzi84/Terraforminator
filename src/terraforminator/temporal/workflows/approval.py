from datetime import timedelta

from temporalio import workflow

from terraforminator.domain.models import ApprovalDecision, ApprovalRecord
from terraforminator.temporal.activities.approval import ApprovalActivities
from terraforminator.temporal.workflows.models import ApprovalWorkflowInput


@workflow.defn
class ApprovalWorkflow:
    def __init__(self) -> None:
        self.approval_record: ApprovalRecord | None = None

    @workflow.run
    async def run(self, input: ApprovalWorkflowInput) -> ApprovalDecision:
        await workflow.wait_condition(lambda: self.approval_record is not None)
        assert self.approval_record is not None
        await workflow.execute_activity_method(
            ApprovalActivities.save_approval,
            self.approval_record,
            start_to_close_timeout=timedelta(seconds=10),
        )
        return self.approval_record.status

    @workflow.signal
    async def record_decision(self, approval_record: ApprovalRecord) -> None:
        if self.approval_record is not None:
            return
        self.approval_record = approval_record
