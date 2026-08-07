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
from app.schemas.aws_discovery import (
    MultiRegionDiscoveryRequest,
    MultiRegionDiscoveryResponse,
    RegionDiscoveryResult,
)

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


@router.post(
    "/discover/{account_id}/multi-region",
    response_model=MultiRegionDiscoveryResponse,
    status_code=status.HTTP_200_OK,
)
def discover_aws_resources_multi_region(
    account_id: uuid.UUID,
    request: MultiRegionDiscoveryRequest,
    database: DatabaseSession,
):
    account = database.get(CloudAccount, account_id)

    if account is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cloud account not found",
        )

    operation_started_at = datetime.now(timezone.utc)
    account.last_sync_at = operation_started_at
    account.last_sync_region = "multi-region"
    database.commit()

    try:
        provider = AWSProvider()
        aws_session = provider.assume_role(
            account.role_arn,
            account.external_id,
        )
        identity = aws_session.client("sts").get_caller_identity()
    except AWSConnectionError as error:
        _register_regions_as_failed(
            database=database,
            account=account,
            regions=request.regions,
            started_at=operation_started_at,
            account_status="connection_failed",
            error_message=(
                "Unable to assume the configured AWS IAM role"
            ),
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unable to assume the configured AWS IAM role",
        ) from error
    except (ClientError, BotoCoreError) as error:
        _register_regions_as_failed(
            database=database,
            account=account,
            regions=request.regions,
            started_at=operation_started_at,
            account_status="connection_failed",
            error_message="AWS rejected the identity validation",
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="AWS rejected the identity validation",
        ) from error

    if identity["Account"] != account.aws_account_id:
        error_message = (
            "The assumed role belongs to a different AWS account"
        )
        _register_regions_as_failed(
            database=database,
            account=account,
            regions=request.regions,
            started_at=operation_started_at,
            account_status="connection_failed",
            error_message=error_message,
        )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=error_message,
        )

    discovered_by_region: dict[str, list[object]] = {}
    region_results: list[RegionDiscoveryResult] = []

    for region in request.regions:
        region_started_at = datetime.now(timezone.utc)
        region_timer = perf_counter()
        sync_run = SyncRun(
            cloud_account_id=account_id,
            region=region,
            status="running",
            resource_count=0,
            started_at=region_started_at,
        )
        database.add(sync_run)
        database.commit()
        database.refresh(sync_run)

        try:
            collector = AWSInventoryCollector(
                session=aws_session,
                region=region,
            )
            region_resources = collector.collect()
            duration_ms = int(
                (perf_counter() - region_timer) * 1000,
            )

            discovered_by_region[region] = region_resources
            sync_run.status = "success"
            sync_run.resource_count = len(region_resources)
            sync_run.duration_ms = duration_ms
            sync_run.error_message = None
            sync_run.completed_at = datetime.now(timezone.utc)
            region_results.append(
                RegionDiscoveryResult(
                    region=region,
                    status="success",
                    resource_count=len(region_resources),
                    duration_ms=duration_ms,
                ),
            )
        except (ClientError, BotoCoreError) as error:
            duration_ms = int(
                (perf_counter() - region_timer) * 1000,
            )
            error_message = _aws_error_message(error)
            sync_run.status = "failed"
            sync_run.duration_ms = duration_ms
            sync_run.error_message = error_message
            sync_run.completed_at = datetime.now(timezone.utc)
            region_results.append(
                RegionDiscoveryResult(
                    region=region,
                    status="failed",
                    resource_count=0,
                    duration_ms=duration_ms,
                    error_message=error_message,
                ),
            )

        database.commit()

    successful_regions = list(discovered_by_region)
    failed_regions = [
        result.region
        for result in region_results
        if result.status == "failed"
    ]

    if not successful_regions:
        account.status = "discovery_failed"
        account.last_sync_status = "failed"
        database.commit()
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="AWS inventory failed in every selected region",
        )

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

    resources: list[CloudResource] = []
    seen_resources: set[tuple[str, str, str]] = set()

    for region_resources in discovered_by_region.values():
        for resource in region_resources:
            resource_key = (
                resource.service,
                resource.resource_id,
                resource.region,
            )

            if resource_key in seen_resources:
                continue

            seen_resources.add(resource_key)
            resources.append(
                CloudResource(
                    cloud_account_id=account_id,
                    service=resource.service,
                    resource_id=resource.resource_id,
                    name=resource.name,
                    region=resource.region,
                    status=resource.status,
                    monthly_cost=resource.monthly_cost,
                    resource_metadata=resource.metadata,
                ),
            )

    database.add_all(resources)

    operation_status = (
        "partial_success" if failed_regions else "success"
    )
    account.status = "connected"
    account.last_sync_status = operation_status
    account.resource_count = len(resources)
    database.commit()

    return MultiRegionDiscoveryResponse(
        cloud_account_id=account_id,
        status=operation_status,
        requested_regions=request.regions,
        successful_regions=successful_regions,
        failed_regions=failed_regions,
        resource_count=len(resources),
        resources=resources,
        region_results=region_results,
    )


def _register_regions_as_failed(
    database: Session,
    account: CloudAccount,
    regions: list[str],
    started_at: datetime,
    account_status: str,
    error_message: str,
) -> None:
    completed_at = datetime.now(timezone.utc)
    duration_ms = max(
        0,
        int((completed_at - started_at).total_seconds() * 1000),
    )

    database.add_all(
        [
            SyncRun(
                cloud_account_id=account.id,
                region=region,
                status="failed",
                resource_count=0,
                duration_ms=duration_ms,
                error_message=error_message,
                started_at=started_at,
                completed_at=completed_at,
            )
            for region in regions
        ],
    )
    account.status = account_status
    account.last_sync_status = "failed"
    database.commit()


def _aws_error_message(error: ClientError | BotoCoreError) -> str:
    if isinstance(error, ClientError):
        aws_error = error.response.get("Error", {})
        code = aws_error.get("Code", "AWS error")
        message = aws_error.get("Message", "Inventory operation failed")
        return f"{code}: {message}"

    return str(error) or "AWS inventory operation failed"
