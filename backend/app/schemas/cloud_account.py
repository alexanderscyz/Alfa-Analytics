import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CloudAccountCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    aws_account_id: str = Field(
        min_length=12,
        max_length=12,
        pattern=r"^\d{12}$",
    )
    role_arn: str = Field(
        min_length=20,
        max_length=255,
        pattern=r"^arn:aws:iam::\d{12}:role/[\w+=,.@/_-]+$",
    )

    @field_validator(
        "name",
        "aws_account_id",
        "role_arn",
        mode="before",
    )
    @classmethod
    def strip_text_fields(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()

        return value


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