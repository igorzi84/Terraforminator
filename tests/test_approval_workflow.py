import asyncio
from dataclasses import replace
from uuid import uuid4

import pytest

from terraforminator.domain.models import ApprovalRecord
from terraforminator.temporal.workflows.approval import ApprovalWorkflow


@pytest.mark.parametrize("first_status", ["approved", "rejected"])
@pytest.mark.parametrize("later_signal", ["duplicate", "conflicting"])
def test_first_approval_signal_wins(first_status, later_signal):
    first_record = ApprovalRecord(
        review_id=uuid4(),
        status=first_status,
        reviewer="Igor",
        reason="First decision",
    )
    later_record = first_record
    if later_signal == "conflicting":
        later_record = replace(
            first_record,
            status="rejected" if first_status == "approved" else "approved",
            reviewer="Another reviewer",
            reason="Conflicting decision",
        )

    async def send_signals():
        # Exercise the handler directly; this does not run a Temporal server.
        approval_workflow = ApprovalWorkflow()
        await approval_workflow.record_decision(first_record)
        assert approval_workflow.approval_record == first_record

        await approval_workflow.record_decision(later_record)
        assert approval_workflow.approval_record == first_record

    asyncio.run(send_signals())
