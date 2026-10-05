from dataclasses import dataclass
from typing import Literal

@dataclass
class DeliveryResult:
    status: Literal["appended", "skipped", "error"]
    anchor: str
    error_message: str | None = None

@dataclass
class EmailDeliveryResult:
    status: Literal["sent", "drafted", "error"]
    draft_id: str | None = None
    message_id: str | None = None
    error_message: str | None = None
