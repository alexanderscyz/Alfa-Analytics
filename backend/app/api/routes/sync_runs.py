import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_database_session
from app.models.cloud_account import CloudAccount
from app.models.sync_run import SyncRun
from app.schemas.sync_run import SyncRunResponse

router = APIRouter(
    prefix="/cloud-accounts",
    tags=["AWS Synchronization History"],
)

DatabaseSession = Annotated[
    Session,
    Depends(get_database_session),
]


@router.get(
    "/{account_id}/sync-runs",
    response_model=list[SyncRunResponse],
)
def list_sync_runs(
    account_id: uuid.UUID,
    database: DatabaseSession,
    limit: int = Query(
        default=10,
        ge=1,
        le=100,
    ),
):
    account = database.get(CloudAccount, account_id)

    if account is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cloud account not found",
        )

    statement = (
        select(SyncRun)
        .where(
            SyncRun.cloud_account_id == account_id,
        )
        .order_by(
            SyncRun.started_at.desc(),
        )
        .limit(limit)
    )

    return database.scalars(statement).all()