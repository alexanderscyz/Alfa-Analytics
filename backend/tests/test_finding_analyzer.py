import uuid
from decimal import Decimal

from app.models.cloud_resource import CloudResource
from app.services.finding_analyzer import analyze_resources


def create_resource(
    service: str,
    name: str,
    status: str,
    monthly_cost: str,
    metadata: dict,
) -> CloudResource:
    return CloudResource(
        id=uuid.uuid4(),
        cloud_account_id=uuid.uuid4(),
        service=service,
        resource_id=f"test-{name}",
        name=name,
        region="us-east-1",
        status=status,
        monthly_cost=Decimal(monthly_cost),
        resource_metadata=metadata,
    )


def test_analyzer_detects_demo_findings():
    resources = [
        create_resource(
            "EC2",
            "worker-stopped",
            "stopped",
            "18.20",
            {"instance_type": "t3.medium"},
        ),
        create_resource(
            "EBS",
            "large-volume",
            "in-use",
            "25.60",
            {"size_gb": 256},
        ),
        create_resource(
            "RDS",
            "production-db",
            "available",
            "146.80",
            {"engine": "postgres"},
        ),
        create_resource(
            "S3",
            "assets-bucket",
            "active",
            "12.35",
            {"storage_gb": 480},
        ),
    ]

    findings = analyze_resources(resources)

    assert len(findings) == 4
    assert {finding.severity for finding in findings} == {
        "high",
        "medium",
    }

    total_savings = sum(
        finding.estimated_savings for finding in findings
    )

    assert total_savings == Decimal("55.24")