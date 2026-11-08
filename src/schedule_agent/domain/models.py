from dataclasses import dataclass
from enum import Enum


class ReviewStatus(str, Enum):
    APPROVED = "approved"
    NEEDS_CONFIRMATION = "needs_confirmation"
    NEED_INFO = "need_info"
    BLOCKED = "blocked"
    UNKNOWN = "unknown"


REVIEW_STATUSES = [s.value for s in ReviewStatus]
CONFIRMATION_STATUSES = ["not_required", "pending", "confirmed"]
SLOT_STATUSES = ["as_requested", "alternative", "none"]
SAVE_RESULTS = ["created", "updated", "duplicate", "failed", "not_saved"]
RUN_STATUSES = ["completed", "completed_with_pending", "save_failed", "incomplete", "failed"]


@dataclass(frozen=True)
class Limits:
    max_steps: int = 15
    max_tool_calls: int = 30
    max_same_call: int = 3

    def __post_init__(self):
        values = (self.max_steps, self.max_tool_calls, self.max_same_call)
        if any(type(value) is not int or value < 1 for value in values):
            raise ValueError("limits must be positive")
