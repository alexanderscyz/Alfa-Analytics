import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class FindingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    cloud_account_id: uuid.UUID
    cloud_resource_id: uuid.UUID
    category: str
    severity: str
    title: str
    description: str
    recommendation: str
    estimated_savings: Decimal
    status: str
    created_at: datetime