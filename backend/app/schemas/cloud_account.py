import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CloudAccountCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    aws_account_id: str = Field(min_length=12, max_length=12)
    role_arn: str = Field(min_length=20, max_length=255)


class CloudAccountResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    provider: str
    aws_account_id: str
    external_id: str | None
    role_arn: str
    status: str
    created_at: datetime