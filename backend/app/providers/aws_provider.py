from dataclasses import dataclass

import boto3
from botocore.exceptions import BotoCoreError, ClientError, NoCredentialsError


class AWSConnectionError(Exception):
    pass


@dataclass
class AWSIdentity:
    account_id: str
    arn: str
    user_id: str


class AWSProvider:
    def __init__(self):
        self.sts_client = boto3.client("sts")

    def assume_role(
        self,
        role_arn: str,
        external_id: str | None = None,
    ) -> boto3.Session:
        request = {
            "RoleArn": role_arn,
            "RoleSessionName": "alfa-analytics",
            "DurationSeconds": 3600,
        }

        if external_id:
            request["ExternalId"] = external_id

        try:
            response = self.sts_client.assume_role(**request)
            credentials = response["Credentials"]

            return boto3.Session(
                aws_access_key_id=credentials["AccessKeyId"],
                aws_secret_access_key=credentials["SecretAccessKey"],
                aws_session_token=credentials["SessionToken"],
            )
        except (ClientError, BotoCoreError, NoCredentialsError) as error:
            raise AWSConnectionError(
                "Unable to assume the configured AWS role",
            ) from error

    def validate_role(
        self,
        role_arn: str,
        external_id: str | None = None,
    ) -> AWSIdentity:
        session = self.assume_role(role_arn, external_id)
        identity = session.client("sts").get_caller_identity()

        return AWSIdentity(
            account_id=identity["Account"],
            arn=identity["Arn"],
            user_id=identity["UserId"],
        )