import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SyncRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    cloud_account_id: uuid.UUID
    region: str
    status: str
    resource_count: int
    duration_ms: int | None
    error_message: str | None
    started_at: datetime
    completed_at: datetime | None