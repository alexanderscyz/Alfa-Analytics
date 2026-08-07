import uuid
from datetime import datetime, timezone
from time import perf_counter
from typing import Annotated

from botocore.exceptions import BotoCoreError, ClientError
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
)
from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.database import get_database_session
from app.models.cloud_account import CloudAccount
from app.models.cloud_resource import CloudResource
from app.models.finding import Finding
from app.models.sync_run import SyncRun
from app.providers.aws_inventory import AWSInventoryCollector
from app.providers.aws_provider import (
    AWSConnectionError,
    AWSProvider,
)
from app.schemas.cloud_resource import CloudResourceResponse

router = APIRouter(prefix="/aws", tags=["AWS Discovery"])

DatabaseSession = Annotated[
    Session,
    Depends(get_database_session),
]


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

    started_at = datetime.now(timezone.utc)
    started_timer = perf_counter()

    sync_run = SyncRun(
        cloud_account_id=account_id,
        region=region,
        status="running",
        resource_count=0,
        started_at=started_at,
    )

    database.add(sync_run)

    account.last_sync_at = started_at
    account.last_sync_region = region

    database.commit()
    database.refresh(sync_run)

    def register_failure(
        account_status: str,
        error_message: str,
    ) -> None:
        completed_at = datetime.now(timezone.utc)

        sync_run.status = "failed"
        sync_run.completed_at = completed_at
        sync_run.duration_ms = int(
            (perf_counter() - started_timer) * 1000,
        )
        sync_run.error_message = error_message

        account.status = account_status
        account.last_sync_status = "failed"

        database.commit()

    try:
        provider = AWSProvider()
        aws_session = provider.assume_role(
            account.role_arn,
            account.external_id,
        )

        identity = aws_session.client(
            "sts",
        ).get_caller_identity()

        if identity["Account"] != account.aws_account_id:
            error_message = (
                "The assumed role belongs to a different "
                "AWS account"
            )

            register_failure(
                account_status="connection_failed",
                error_message=error_message,
            )

            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=error_message,
            )

        collector = AWSInventoryCollector(
            session=aws_session,
            region=region,
        )
        discovered_resources = collector.collect()

    except AWSConnectionError as error:
        error_message = (
            "Unable to assume the configured AWS IAM role"
        )

        register_failure(
            account_status="connection_failed",
            error_message=error_message,
        )

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=error_message,
        ) from error

    except (ClientError, BotoCoreError) as error:
        error_message = (
            "AWS rejected one or more inventory operations"
        )

        register_failure(
            account_status="discovery_failed",
            error_message=error_message,
        )

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=error_message,
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

    completed_at = datetime.now(timezone.utc)

    sync_run.status = "success"
    sync_run.resource_count = len(resources)
    sync_run.duration_ms = int(
        (perf_counter() - started_timer) * 1000,
    )
    sync_run.error_message = None
    sync_run.completed_at = completed_at

    account.status = "connected"
    account.last_sync_status = "success"
    account.resource_count = len(resources)

    database.commit()

    return resources