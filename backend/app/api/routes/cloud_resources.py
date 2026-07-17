import uuid
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import delete
from app.models.cloud_account import CloudAccount
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_database_session
from app.models.cloud_resource import CloudResource
from app.schemas.cloud_resource import CloudResourceResponse

router = APIRouter(prefix="/cloud-resources", tags=["Cloud Resources"])

DatabaseSession = Annotated[Session, Depends(get_database_session)]


@router.get("/", response_model=list[CloudResourceResponse])
def list_cloud_resources(database: DatabaseSession):
    statement = select(CloudResource).order_by(
        CloudResource.discovered_at.desc(),
    )

    return database.scalars(statement).all()

@router.post(
    "/demo/{account_id}",
    response_model=list[CloudResourceResponse],
    status_code=status.HTTP_201_CREATED,
)
def generate_demo_inventory(
    account_id: uuid.UUID,
    database: DatabaseSession,
):
    account = database.get(CloudAccount, account_id)

    if account is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cloud account not found",
        )

    database.execute(
        delete(CloudResource).where(
            CloudResource.cloud_account_id == account_id,
        ),
    )

    demo_resources = [
        CloudResource(
            cloud_account_id=account_id,
            service="EC2",
            resource_id="i-0a12bc34de56f7890",
            name="web-production-01",
            region="us-east-1",
            status="running",
            monthly_cost=Decimal("82.40"),
            resource_metadata={"instance_type": "t3.large"},
        ),
        CloudResource(
            cloud_account_id=account_id,
            service="EC2",
            resource_id="i-0b98fe76dc54a3210",
            name="worker-production-01",
            region="us-east-1",
            status="stopped",
            monthly_cost=Decimal("18.20"),
            resource_metadata={"instance_type": "t3.medium"},
        ),
        CloudResource(
            cloud_account_id=account_id,
            service="RDS",
            resource_id="alfa-production-db",
            name="alfa-production-db",
            region="us-east-1",
            status="available",
            monthly_cost=Decimal("146.80"),
            resource_metadata={"engine": "postgres"},
        ),
        CloudResource(
            cloud_account_id=account_id,
            service="S3",
            resource_id="alfa-production-assets",
            name="alfa-production-assets",
            region="us-east-1",
            status="active",
            monthly_cost=Decimal("12.35"),
            resource_metadata={"storage_gb": 480},
        ),
        CloudResource(
            cloud_account_id=account_id,
            service="EBS",
            resource_id="vol-0123456789abcdef0",
            name="web-production-volume",
            region="us-east-1",
            status="in-use",
            monthly_cost=Decimal("25.60"),
            resource_metadata={"size_gb": 256},
        ),
        CloudResource(
            cloud_account_id=account_id,
            service="EKS",
            resource_id="alfa-production-cluster",
            name="alfa-production-cluster",
            region="us-east-1",
            status="active",
            monthly_cost=Decimal("73.00"),
            resource_metadata={"version": "1.34"},
        ),
        CloudResource(
            cloud_account_id=account_id,
            service="Lambda",
            resource_id="daily-cost-analyzer",
            name="daily-cost-analyzer",
            region="us-east-1",
            status="active",
            monthly_cost=Decimal("3.25"),
            resource_metadata={"runtime": "python3.12"},
        ),
    ]

    database.add_all(demo_resources)
    account.status = "demo"
    database.commit()

    return demo_resources