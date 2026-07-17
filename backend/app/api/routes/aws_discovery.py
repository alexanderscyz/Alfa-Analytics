import uuid
from typing import Annotated

from botocore.exceptions import BotoCoreError, ClientError
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.database import get_database_session
from app.models.cloud_account import CloudAccount
from app.models.cloud_resource import CloudResource
from app.models.finding import Finding
from app.providers.aws_inventory import AWSInventoryCollector
from app.providers.aws_provider import AWSConnectionError, AWSProvider
from app.schemas.cloud_resource import CloudResourceResponse

router = APIRouter(prefix="/aws", tags=["AWS Discovery"])

DatabaseSession = Annotated[Session, Depends(get_database_session)]


@router.post(
    "/discover/{account_id}",
    response_model=list[CloudResourceResponse],
    status_code=status.HTTP_201_CREATED,
)
def discover_aws_resources(
    account_id: uuid.UUID,
    database: DatabaseSession,
    region: str = Query(
        default="us-east-1",
        min_length=3,
        max_length=30,
    ),
):
    account = database.get(CloudAccount, account_id)

    if account is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cloud account not found",
        )

    try:
        provider = AWSProvider()
        aws_session = provider.assume_role(account.role_arn)

        identity = aws_session.client("sts").get_caller_identity()

        if identity["Account"] != account.aws_account_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "The assumed role belongs to a different AWS account"
                ),
            )

        collector = AWSInventoryCollector(
            session=aws_session,
            region=region,
        )
        discovered_resources = collector.collect()

    except AWSConnectionError as error:
        account.status = "connection_failed"
        database.commit()

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=(
                "Unable to assume the configured AWS IAM role"
            ),
        ) from error

    except (ClientError, BotoCoreError) as error:
        account.status = "discovery_failed"
        database.commit()

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=(
                "AWS rejected one or more inventory operations"
            ),
        ) from error

    database.execute(
        delete(Finding).where(
            Finding.cloud_account_id == account_id,
        ),
    )

    database.execute(
        delete(CloudResource).where(
            CloudResource.cloud_account_id == account_id,
        ),
    )

    resources = [
        CloudResource(
            cloud_account_id=account_id,
            service=resource.service,
            resource_id=resource.resource_id,
            name=resource.name,
            region=resource.region,
            status=resource.status,
            monthly_cost=resource.monthly_cost,
            resource_metadata=resource.metadata,
        )
        for resource in discovered_resources
    ]

    database.add_all(resources)
    account.status = "connected"
    database.commit()

    return resources