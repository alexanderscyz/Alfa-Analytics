from dataclasses import dataclass, field
from decimal import Decimal

import boto3


@dataclass
class DiscoveredResource:
    service: str
    resource_id: str
    name: str
    region: str
    status: str
    monthly_cost: Decimal = Decimal("0")
    metadata: dict = field(default_factory=dict)


class AWSInventoryCollector:
    def __init__(
        self,
        session: boto3.Session,
        region: str = "us-east-1",
    ):
        self.session = session
        self.region = region

    @staticmethod
    def get_name(tags: list[dict] | None, fallback: str) -> str:
        for tag in tags or []:
            if tag.get("Key") == "Name" and tag.get("Value"):
                return tag["Value"]

        return fallback

    def collect_ec2_instances(self) -> list[DiscoveredResource]:
        client = self.session.client("ec2", region_name=self.region)
        paginator = client.get_paginator("describe_instances")
        resources: list[DiscoveredResource] = []

        for page in paginator.paginate():
            for reservation in page.get("Reservations", []):
                for instance in reservation.get("Instances", []):
                    instance_id = instance["InstanceId"]

                    resources.append(
                        DiscoveredResource(
                            service="EC2",
                            resource_id=instance_id,
                            name=self.get_name(
                                instance.get("Tags"),
                                instance_id,
                            ),
                            region=self.region,
                            status=instance["State"]["Name"],
                            metadata={
                                "instance_type": instance.get(
                                    "InstanceType",
                                ),
                                "availability_zone": instance.get(
                                    "Placement",
                                    {},
                                ).get("AvailabilityZone"),
                                "private_ip": instance.get(
                                    "PrivateIpAddress",
                                ),
                                "public_ip": instance.get(
                                    "PublicIpAddress",
                                ),
                                "architecture": instance.get(
                                    "Architecture",
                                ),
                                "tags": instance.get("Tags", []),
                            },
                        ),
                    )

        return resources

    def collect_ebs_volumes(self) -> list[DiscoveredResource]:
        client = self.session.client("ec2", region_name=self.region)
        paginator = client.get_paginator("describe_volumes")
        resources: list[DiscoveredResource] = []

        for page in paginator.paginate():
            for volume in page.get("Volumes", []):
                volume_id = volume["VolumeId"]

                resources.append(
                    DiscoveredResource(
                        service="EBS",
                        resource_id=volume_id,
                        name=self.get_name(
                            volume.get("Tags"),
                            volume_id,
                        ),
                        region=self.region,
                        status=volume["State"],
                        metadata={
                            "size_gb": volume.get("Size"),
                            "volume_type": volume.get("VolumeType"),
                            "encrypted": volume.get("Encrypted"),
                            "iops": volume.get("Iops"),
                            "attachments": volume.get(
                                "Attachments",
                                [],
                            ),
                            "tags": volume.get("Tags", []),
                        },
                    ),
                )

        return resources

    def collect_rds_instances(self) -> list[DiscoveredResource]:
        client = self.session.client("rds", region_name=self.region)
        paginator = client.get_paginator("describe_db_instances")
        resources: list[DiscoveredResource] = []

        for page in paginator.paginate():
            for database in page.get("DBInstances", []):
                identifier = database["DBInstanceIdentifier"]

                resources.append(
                    DiscoveredResource(
                        service="RDS",
                        resource_id=identifier,
                        name=identifier,
                        region=self.region,
                        status=database["DBInstanceStatus"],
                        metadata={
                            "engine": database.get("Engine"),
                            "engine_version": database.get(
                                "EngineVersion",
                            ),
                            "instance_class": database.get(
                                "DBInstanceClass",
                            ),
                            "storage_gb": database.get(
                                "AllocatedStorage",
                            ),
                            "encrypted": database.get(
                                "StorageEncrypted",
                            ),
                            "multi_az": database.get("MultiAZ"),
                            "publicly_accessible": database.get(
                                "PubliclyAccessible",
                            ),
                        },
                    ),
                )

        return resources

    def collect_s3_buckets(self) -> list[DiscoveredResource]:
        client = self.session.client("s3")
        resources: list[DiscoveredResource] = []

        for bucket in client.list_buckets().get("Buckets", []):
            bucket_name = bucket["Name"]

            location = client.get_bucket_location(
                Bucket=bucket_name,
            ).get("LocationConstraint")

            bucket_region = location or "us-east-1"

            if bucket_region == "EU":
                bucket_region = "eu-west-1"

            resources.append(
                DiscoveredResource(
                    service="S3",
                    resource_id=bucket_name,
                    name=bucket_name,
                    region=bucket_region,
                    status="active",
                    metadata={
                        "creation_date": bucket[
                            "CreationDate"
                        ].isoformat(),
                    },
                ),
            )

        return resources

    def collect_eks_clusters(self) -> list[DiscoveredResource]:
        client = self.session.client("eks", region_name=self.region)
        paginator = client.get_paginator("list_clusters")
        resources: list[DiscoveredResource] = []

        for page in paginator.paginate():
            for cluster_name in page.get("clusters", []):
                cluster = client.describe_cluster(
                    name=cluster_name,
                )["cluster"]

                resources.append(
                    DiscoveredResource(
                        service="EKS",
                        resource_id=cluster["arn"],
                        name=cluster["name"],
                        region=self.region,
                        status=cluster["status"].lower(),
                        metadata={
                            "version": cluster.get("version"),
                            "endpoint_public": cluster.get(
                                "resourcesVpcConfig",
                                {},
                            ).get("endpointPublicAccess"),
                            "endpoint_private": cluster.get(
                                "resourcesVpcConfig",
                                {},
                            ).get("endpointPrivateAccess"),
                            "tags": cluster.get("tags", {}),
                        },
                    ),
                )

        return resources

    def collect_lambda_functions(self) -> list[DiscoveredResource]:
        client = self.session.client(
            "lambda",
            region_name=self.region,
        )
        paginator = client.get_paginator("list_functions")
        resources: list[DiscoveredResource] = []

        for page in paginator.paginate():
            for function in page.get("Functions", []):
                resources.append(
                    DiscoveredResource(
                        service="Lambda",
                        resource_id=function["FunctionArn"],
                        name=function["FunctionName"],
                        region=self.region,
                        status=function.get(
                            "State",
                            "active",
                        ).lower(),
                        metadata={
                            "runtime": function.get("Runtime"),
                            "memory_mb": function.get(
                                "MemorySize",
                            ),
                            "timeout_seconds": function.get(
                                "Timeout",
                            ),
                            "package_type": function.get(
                                "PackageType",
                            ),
                            "last_modified": function.get(
                                "LastModified",
                            ),
                        },
                    ),
                )

        return resources

    def collect(self) -> list[DiscoveredResource]:
        return [
            *self.collect_ec2_instances(),
            *self.collect_ebs_volumes(),
            *self.collect_rds_instances(),
            *self.collect_s3_buckets(),
            *self.collect_eks_clusters(),
            *self.collect_lambda_functions(),
        ]