import json
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.database import get_database_session
from app.models.cloud_account import CloudAccount
from app.schemas.cloud_account import (
    CloudAccountCreate,
    CloudAccountResponse,
)
from app.services.cloudformation import (
    build_aws_onboarding_template,
)


router = APIRouter(
    prefix="/cloud-accounts",
    tags=["Cloud Accounts"],
)

DatabaseSession = Annotated[
    Session,
    Depends(get_database_session),
]
ApplicationSettings = Annotated[
    Settings,
    Depends(get_settings),
]


@router.get(
    "/",
    response_model=list[CloudAccountResponse],
)
def list_cloud_accounts(database: DatabaseSession):
    statement = select(CloudAccount).order_by(
        CloudAccount.created_at.desc(),
    )
    return database.scalars(statement).all()


@router.post(
    "/",
    response_model=CloudAccountResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_cloud_account(
    account_data: CloudAccountCreate,
    database: DatabaseSession,
):

    role_arn = (
        f"arn:aws:iam::{account_data.aws_account_id}:"
        "role/AlfaAnalyticsReadOnlyRole"
    )

    account = CloudAccount(
        **account_data.model_dump(),
        role_arn=role_arn,
    )

    try:
        database.add(account)
        database.commit()
        database.refresh(account)
    except IntegrityError:
        database.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The AWS account is already registered",
        )

    return account


@router.get(
    "/{account_id}/cloudformation",
    response_class=Response,
)
def download_cloudformation_template(
    account_id: uuid.UUID,
    database: DatabaseSession,
    settings: ApplicationSettings,
):
    account = database.get(CloudAccount, account_id)

    if account is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cloud account not found",
        )

    if account.external_id is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The cloud account does not have an External ID",
        )

    trusted_principal_arn = settings.aws_trusted_principal_arn

    if not trusted_principal_arn:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "ALFA_AWS_PRINCIPAL_ARN is not configured"
            ),
        )

    if (
        not trusted_principal_arn.startswith("arn:aws:iam::")
        or ":role/" not in trusted_principal_arn
    ):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "ALFA_AWS_PRINCIPAL_ARN is not a valid IAM role ARN"
            ),
        )

    template = build_aws_onboarding_template(
        trusted_principal_arn=trusted_principal_arn,
        external_id=account.external_id,
    )

    filename = (
        f"alfa-analytics-{account.id}-cloudformation.json"
    )

    return Response(
        content=json.dumps(template, indent=2),
        media_type="application/json",
        headers={
            "Content-Disposition": (
                f'attachment; filename="{filename}"'
            ),
        },
    )


@router.delete(
    "/{account_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_cloud_account(
    account_id: uuid.UUID,
    database: DatabaseSession,
):
    account = database.get(CloudAccount, account_id)

    if account is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cloud account not found",
        )

    database.delete(account)
    database.commit()