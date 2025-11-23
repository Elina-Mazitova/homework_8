from enum import StrEnum

class Status(StrEnum):
    DRAFT = "draft"
    READY = "ready"
    SENT = "sent"
    FAILED = "failed"
    INVALID = "invalid"
