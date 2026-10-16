import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor

from temporalio.client import Client
from temporalio.worker import Worker

from terraforminator.config import load_app_settings
from terraforminator.logging_config import configure_logging
from terraforminator.sqlite_review_store import SQLiteReviewStore
from terraforminator.temporal.activities.approval import ApprovalActivities
from terraforminator.temporal.workflows.approval import ApprovalWorkflow

logger = logging.getLogger("terraforminator.worker")


async def main():
    configure_logging()
    settings = load_app_settings()

    client = await Client.connect(settings.temporal_address)

    review_store = SQLiteReviewStore(settings.database_path)
    approval_activities = ApprovalActivities(review_store)

    with ThreadPoolExecutor(max_workers=4) as executor:
        worker = Worker(
            client,
            task_queue="terraforminator-approval",
            workflows=[ApprovalWorkflow],
            activities=[approval_activities.save_approval],
            activity_executor=executor,
        )
        logger.info("Starting Temporal Worker")
        await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
