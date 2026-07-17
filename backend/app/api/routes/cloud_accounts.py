from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_database_session
from app.models.cloud_account import CloudAccount
from app.schemas.cloud_account import CloudAccountCreate, CloudAccountResponse

router = APIRouter(prefix="/cloud-accounts", tags=["Cloud Accounts"])

DatabaseSession = Annotated[Session, Depends(get_database_session)]


@router.get("/", response_model=list[CloudAccountResponse])
def list_cloud_accounts(database: DatabaseSession):
    statement = select(CloudAccount).order_by(CloudAccount.created_at.desc())
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
    account = CloudAccount(**account_data.model_dump())

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