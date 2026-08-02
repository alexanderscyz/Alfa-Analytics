import uuid
from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes.cloud_accounts import router
from app.core.config import Settings, get_settings
from app.database import get_database_session


ACCOUNT_ID = uuid.UUID(
    "12345678-1234-5678-1234-567812345678"
)
EXTERNAL_ID = "test-external-id"
TRUSTED_PRINCIPAL_ARN = (
    "arn:aws:iam::123456789012:"
    "role/AlfaAnalyticsBackendRole"
)


class FakeDatabase:
    def __init__(self, account: object | None):
        self.account = account

    def get(
        self,
        model: object,
        account_id: uuid.UUID,
    ) -> object | None:
        del model

        if (
            self.account is not None
            and getattr(self.account, "id") == account_id
        ):
            return self.account

        return None


def create_test_client(
    *,
    account: object | None,
    trusted_principal_arn: str | None,
) -> TestClient:
    application = FastAPI()
    application.include_router(router, prefix="/api/v1")

    application.dependency_overrides[
        get_database_session
    ] = lambda: FakeDatabase(account)

    application.dependency_overrides[
        get_settings
    ] = lambda: Settings(
        aws_trusted_principal_arn=trusted_principal_arn,
    )

    return TestClient(application)


def test_download_cloudformation_template() -> None:
    account = SimpleNamespace(
        id=ACCOUNT_ID,
        external_id=EXTERNAL_ID,
    )
    client = create_test_client(
        account=account,
        trusted_principal_arn=TRUSTED_PRINCIPAL_ARN,
    )

    response = client.get(
        f"/api/v1/cloud-accounts/{ACCOUNT_ID}/cloudformation"
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith(
        "application/json"
    )
    assert response.headers["content-disposition"] == (
        "attachment; filename="
        f'"alfa-analytics-{ACCOUNT_ID}-cloudformation.json"'
    )

    template = response.json()
    role = template["Resources"]["AlfaAnalyticsReadOnlyRole"]
    trust_statement = role["Properties"][
        "AssumeRolePolicyDocument"
    ]["Statement"][0]

    assert trust_statement["Principal"]["AWS"] == (
        TRUSTED_PRINCIPAL_ARN
    )
    assert trust_statement["Condition"]["StringEquals"][
        "sts:ExternalId"
    ] == EXTERNAL_ID


def test_cloudformation_returns_404_for_unknown_account() -> None:
    client = create_test_client(
        account=None,
        trusted_principal_arn=TRUSTED_PRINCIPAL_ARN,
    )

    response = client.get(
        f"/api/v1/cloud-accounts/{ACCOUNT_ID}/cloudformation"
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Cloud account not found",
    }


def test_cloudformation_returns_503_without_principal() -> None:
    account = SimpleNamespace(
        id=ACCOUNT_ID,
        external_id=EXTERNAL_ID,
    )
    client = create_test_client(
        account=account,
        trusted_principal_arn=None,
    )

    response = client.get(
        f"/api/v1/cloud-accounts/{ACCOUNT_ID}/cloudformation"
    )

    assert response.status_code == 503
    assert response.json() == {
        "detail": (
            "ALFA_AWS_PRINCIPAL_ARN is not configured"
        ),
    }