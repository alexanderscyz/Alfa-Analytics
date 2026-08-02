import pytest
from pydantic import ValidationError

from app.schemas.cloud_account import CloudAccountCreate


def test_cloud_account_create_strips_whitespace() -> None:
    account = CloudAccountCreate(
        name=" Prueba ",
        aws_account_id=" 123456789012 ",
        role_arn=" arn:aws:iam::123456789012:role/TestRole ",
    )

    assert account.name == "Prueba"
    assert account.aws_account_id == "123456789012"
    assert account.role_arn == (
        "arn:aws:iam::123456789012:role/TestRole"
    )


@pytest.mark.parametrize(
    ("aws_account_id", "role_arn"),
    [
        (
            "1234",
            "arn:aws:iam::123456789012:role/TestRole",
        ),
        (
            "123456789012",
            "not-an-iam-role-arn",
        ),
    ],
)
def test_cloud_account_create_rejects_invalid_aws_data(
    aws_account_id: str,
    role_arn: str,
) -> None:
    with pytest.raises(ValidationError):
        CloudAccountCreate(
            name="Prueba",
            aws_account_id=aws_account_id,
            role_arn=role_arn,
        )