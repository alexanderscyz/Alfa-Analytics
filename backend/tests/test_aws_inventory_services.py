from datetime import datetime, timezone

from app.providers.aws_inventory import AWSInventoryCollector


class FakePaginator:
    def __init__(self, pages: list[dict]):
        self.pages = pages

    def paginate(self) -> list[dict]:
        return self.pages


class FakeELBV2Client:
    def get_paginator(self, operation_name: str) -> FakePaginator:
        assert operation_name == "describe_load_balancers"
        return FakePaginator(
            [
                {
                    "LoadBalancers": [
                        {
                            "LoadBalancerArn": "arn:aws:elb:alb-1",
                            "LoadBalancerName": "public-alb",
                            "Type": "application",
                            "State": {"Code": "active"},
                            "Scheme": "internet-facing",
                            "DNSName": "public.example.com",
                            "VpcId": "vpc-123",
                            "IpAddressType": "ipv4",
                            "SecurityGroups": ["sg-123"],
                            "AvailabilityZones": [
                                {"ZoneName": "us-east-1a"},
                            ],
                        },
                        {
                            "LoadBalancerArn": "arn:aws:elb:nlb-1",
                            "LoadBalancerName": "private-nlb",
                            "Type": "network",
                            "State": {"Code": "active"},
                        },
                    ],
                },
            ],
        )

    def describe_tags(
        self,
        ResourceArns: list[str],
    ) -> dict:
        return {
            "TagDescriptions": [
                {
                    "ResourceArn": resource_arn,
                    "Tags": [{"Key": "Environment", "Value": "prod"}],
                }
                for resource_arn in ResourceArns
            ],
        }


class FakeEC2Client:
    def get_paginator(self, operation_name: str) -> FakePaginator:
        assert operation_name == "describe_nat_gateways"
        return FakePaginator(
            [
                {
                    "NatGateways": [
                        {
                            "NatGatewayId": "nat-123",
                            "State": "available",
                            "VpcId": "vpc-123",
                            "SubnetId": "subnet-123",
                            "ConnectivityType": "public",
                            "NatGatewayAddresses": [
                                {"PublicIp": "203.0.113.10"},
                            ],
                            "CreateTime": datetime(
                                2026,
                                8,
                                7,
                                tzinfo=timezone.utc,
                            ),
                            "Tags": [
                                {"Key": "Name", "Value": "main-nat"},
                            ],
                        },
                    ],
                },
            ],
        )


class FakeS3Client:
    def list_buckets(self) -> dict:
        created_at = datetime(2026, 8, 7, tzinfo=timezone.utc)
        return {
            "Buckets": [
                {"Name": "east-bucket", "CreationDate": created_at},
                {"Name": "south-bucket", "CreationDate": created_at},
            ],
        }

    def get_bucket_location(self, Bucket: str) -> dict:
        return {
            "LocationConstraint": (
                None if Bucket == "east-bucket" else "sa-east-1"
            ),
        }


class FakeSession:
    def __init__(self):
        self.elbv2 = FakeELBV2Client()
        self.ec2 = FakeEC2Client()
        self.s3 = FakeS3Client()

    def client(
        self,
        service_name: str,
        region_name: str | None = None,
    ) -> object:
        if service_name == "elbv2":
            assert region_name == "us-east-1"
            return self.elbv2

        if service_name == "ec2":
            assert region_name == "us-east-1"
            return self.ec2

        if service_name == "s3":
            assert region_name is None
            return self.s3

        raise AssertionError(f"Unexpected AWS service: {service_name}")


def test_collect_load_balancers_distinguishes_alb_and_nlb() -> None:
    collector = AWSInventoryCollector(
        session=FakeSession(),
        region="us-east-1",
    )

    resources = collector.collect_load_balancers()

    assert [resource.service for resource in resources] == [
        "ALB",
        "NLB",
    ]
    assert resources[0].name == "public-alb"
    assert resources[0].status == "active"
    assert resources[0].metadata["vpc_id"] == "vpc-123"
    assert resources[0].metadata["tags"] == [
        {"Key": "Environment", "Value": "prod"},
    ]


def test_collect_nat_gateways_includes_network_metadata() -> None:
    collector = AWSInventoryCollector(
        session=FakeSession(),
        region="us-east-1",
    )

    resources = collector.collect_nat_gateways()

    assert len(resources) == 1
    assert resources[0].service == "NAT Gateway"
    assert resources[0].name == "main-nat"
    assert resources[0].status == "available"
    assert resources[0].metadata["connectivity_type"] == "public"
    assert resources[0].metadata["vpc_id"] == "vpc-123"
    assert resources[0].metadata["subnet_id"] == "subnet-123"
    assert resources[0].metadata["addresses"] == [
        {"PublicIp": "203.0.113.10"},
    ]


def test_collect_s3_buckets_returns_only_selected_region() -> None:
    collector = AWSInventoryCollector(
        session=FakeSession(),
        region="us-east-1",
    )

    resources = collector.collect_s3_buckets()

    assert [resource.name for resource in resources] == [
        "east-bucket",
    ]
    assert resources[0].region == "us-east-1"
