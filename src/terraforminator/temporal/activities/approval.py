from temporalio import activity

from terraforminator.domain.models import ApprovalRecord
from terraforminator.review_store import ReviewStore


class ApprovalActivities:
    def __init__(self, store: ReviewStore) -> None:
        self.store = store

    @activity.defn(name="save_approval")
    def save_approval(self, approval_record: ApprovalRecord) -> None:
        self.store.save_approval(approval_record)
