import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.database import get_database_session
from app.models.cloud_account import CloudAccount
from app.models.cloud_resource import CloudResource
from app.models.finding import Finding
from app.schemas.finding import FindingResponse
from app.services.finding_analyzer import analyze_resources

router = APIRouter(prefix="/findings", tags=["Findings"])

DatabaseSession = Annotated[Session, Depends(get_database_session)]


@router.get("/", response_model=list[FindingResponse])
def list_findings(database: DatabaseSession):
    statement = select(Finding).order_by(Finding.created_at.desc())
    return database.scalars(statement).all()


@router.post(
    "/analyze/{account_id}",
    response_model=list[FindingResponse],
    status_code=status.HTTP_201_CREATED,
)
def analyze_cloud_account(
    account_id: uuid.UUID,
    database: DatabaseSession,
):
    account = database.get(CloudAccount, account_id)

    if account is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cloud account not found",
        )

    resources = list(
        database.scalars(
            select(CloudResource).where(
                CloudResource.cloud_account_id == account_id,
            ),
        ).all(),
    )

    if not resources:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The account does not have discovered resources",
        )

    database.execute(
        delete(Finding).where(
            Finding.cloud_account_id == account_id,
        ),
    )

    findings = analyze_resources(resources)
    database.add_all(findings)
    database.commit()

    return findings