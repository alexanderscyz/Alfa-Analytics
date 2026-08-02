import os
from dataclasses import dataclass
from functools import lru_cache


@dataclass(frozen=True)
class Settings:
    aws_trusted_principal_arn: str | None


@lru_cache
def get_settings() -> Settings:
    return Settings(
        aws_trusted_principal_arn=os.getenv(
            "ALFA_AWS_PRINCIPAL_ARN",
        ),
    )