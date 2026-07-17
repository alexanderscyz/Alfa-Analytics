import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_database_session
from app.models.cloud_account import CloudAccount
from app.models.cloud_resource import CloudResource
from app.models.finding import Finding
from app.services.report_generator import generate_executive_report

router = APIRouter(prefix="/reports", tags=["Reports"])

DatabaseSession = Annotated[Session, Depends(get_database_session)]


@router.get("/{account_id}/executive")
def download_executive_report(
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

    findings = list(
        database.scalars(
            select(Finding).where(
                Finding.cloud_account_id == account_id,
            ),
        ).all(),
    )

    if not resources:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The account does not have discovered resources",
        )

    pdf = generate_executive_report(account, resources, findings)

    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={
            "Content-Disposition": (
                'attachment; filename="alfa-analytics-report.pdf"'
            ),
        },
    )