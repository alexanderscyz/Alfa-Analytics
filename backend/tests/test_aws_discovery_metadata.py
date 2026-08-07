import uuid
from decimal import Decimal
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.api.routes import aws_discovery
from app.models.sync_run import SyncRun
from app.providers.aws_provider import AWSConnectionError

ACCOUNT_ID = uuid.UUID(
    "12345678-1234-5678-1234-567812345678",
)


class FakeDatabase:
    def __init__(self, account: object):
        self.account = account
        self.commits = 0
        self.added_objects: list[object] = []
        self.saved_resources: list[object] = []
        self.executed_statements: list[object] = []

    def get(
        self,
        model: object,
        account_id: uuid.UUID,
    ) -> object | None:
        del model

        if (
            account_id == ACCOUNT_ID
            and getattr(self.account, "id") == account_id
        ):
            return self.account

        return None

    def add(self, instance: object) -> None:
        self.added_objects.append(instance)

    def refresh(self, instance: object) -> None:
        del instance

    def execute(self, statement: object) -> None:
        self.executed_statements.append(statement)

    def add_all(self, resources: list[object]) -> None:
        self.saved_resources.extend(resources)

    def commit(self) -> None:
        self.commits += 1

    def get_sync_run(self) -> SyncRun:
        sync_runs = [
            instance
            for instance in self.added_objects
            if isinstance(instance, SyncRun)
        ]

        assert len(sync_runs) == 1
        return sync_runs[0]


class FakeSTSClient:
    def get_caller_identity(self) -> dict[str, str]:
        return {
            "Account": "123456789012",
            "Arn": (
                "arn:aws:sts::123456789012:"
                "assumed-role/Test/test"
            ),
            "UserId": "test-user",
        }


class FakeAWSSession:
    def client(self, service_name: str) -> FakeSTSClient:
        assert service_name == "sts"
        return FakeSTSClient()


def create_account() -> SimpleNamespace:
    return SimpleNamespace(
        id=ACCOUNT_ID,
        aws_account_id="123456789012",
        role_arn=(
            "arn:aws:iam::123456789012:"
            "role/AlfaAnalyticsReadOnlyRole"
        ),
        external_id="test-external-id",
        status="pending",
        last_sync_at=None,
        last_sync_region=None,
        last_sync_status=None,
        resource_count=0,
    )


def test_successful_discovery_updates_sync_metadata(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    account = create_account()
    database = FakeDatabase(account)

    provider = SimpleNamespace(
        assume_role=(
            lambda role_arn, external_id: FakeAWSSession()
        ),
    )

    discovered_resource = SimpleNamespace(
        service="EC2",
        resource_id="i-1234567890",
        name="test-instance",
        region="us-east-1",
        status="running",
        monthly_cost=Decimal("0"),
        metadata={},
    )

    collector = SimpleNamespace(
        collect=lambda: [discovered_resource],
    )

    monkeypatch.setattr(
        aws_discovery,
        "AWSProvider",
        lambda: provider,
    )
    monkeypatch.setattr(
        aws_discovery,
        "AWSInventoryCollector",
        lambda session, region: collector,
    )

    resources = aws_discovery.discover_aws_resources(
        account_id=ACCOUNT_ID,
        database=database,
        region="us-east-1",
    )

    sync_run = database.get_sync_run()

    assert len(resources) == 1
    assert account.status == "connected"
    assert account.last_sync_at is not None
    assert account.last_sync_region == "us-east-1"
    assert account.last_sync_status == "success"
    assert account.resource_count == 1

    assert sync_run.cloud_account_id == ACCOUNT_ID
    assert sync_run.region == "us-east-1"
    assert sync_run.status == "success"
    assert sync_run.resource_count == 1
    assert sync_run.duration_ms is not None
    assert sync_run.duration_ms >= 0
    assert sync_run.error_message is None
    assert sync_run.started_at is not None
    assert sync_run.completed_at is not None

    assert database.commits == 2
    assert len(database.saved_resources) == 1


def test_failed_connection_updates_sync_metadata(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    account = create_account()
    database = FakeDatabase(account)

    def fail_assume_role(
        role_arn: str,
        external_id: str | None,
    ) -> None:
        del role_arn, external_id
        raise AWSConnectionError("Connection failed")

    provider = SimpleNamespace(
        assume_role=fail_assume_role,
    )

    monkeypatch.setattr(
        aws_discovery,
        "AWSProvider",
        lambda: provider,
    )

    with pytest.raises(HTTPException) as captured_error:
        aws_discovery.discover_aws_resources(
            account_id=ACCOUNT_ID,
            database=database,
            region="us-west-2",
        )

    sync_run = database.get_sync_run()

    assert captured_error.value.status_code == 502
    assert account.status == "connection_failed"
    assert account.last_sync_at is not None
    assert account.last_sync_region == "us-west-2"
    assert account.last_sync_status == "failed"
    assert account.resource_count == 0

    assert sync_run.cloud_account_id == ACCOUNT_ID
    assert sync_run.region == "us-west-2"
    assert sync_run.status == "failed"
    assert sync_run.resource_count == 0
    assert sync_run.duration_ms is not None
    assert sync_run.duration_ms >= 0
    assert sync_run.error_message == (
        "Unable to assume the configured AWS IAM role"
    )
    assert sync_run.started_at is not None
    assert sync_run.completed_at is not None

    assert database.commits == 2