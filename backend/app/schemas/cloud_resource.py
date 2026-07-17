import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class CloudResourceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    cloud_account_id: uuid.UUID
    service: str
    resource_id: str
    name: str
    region: str
    status: str
    monthly_cost: Decimal
    resource_metadata: dict
    discovered_at: datetime