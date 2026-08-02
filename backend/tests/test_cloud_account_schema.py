import pytest
from pydantic import ValidationError

from app.schemas.cloud_account import CloudAccountCreate


def test_cloud_account_create_strips_whitespace() -> None:
    account = CloudAccountCreate(
        name=" Prueba ",
        aws_account_id=" 123456789012 ",
    )

    assert account.name == "Prueba"
    assert account.aws_account_id == "123456789012"


@pytest.mark.parametrize(
    "aws_account_id",
    [
        "1234",
        "12345678901a",
        "1234567890123",
    ],
)
def test_cloud_account_create_rejects_invalid_account_id(
    aws_account_id: str,
) -> None:
    with pytest.raises(ValidationError):
        CloudAccountCreate(
            name="Prueba",
            aws_account_id=aws_account_id,
        )