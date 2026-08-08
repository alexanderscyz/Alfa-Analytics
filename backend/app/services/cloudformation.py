from typing import Any


INVENTORY_READ_ACTIONS = [
    "ec2:DescribeInstances",
    "ec2:DescribeNatGateways",
    "ec2:DescribeVolumes",
    "elasticloadbalancing:DescribeLoadBalancers",
    "elasticloadbalancing:DescribeTags",
    "rds:DescribeDBInstances",
    "s3:ListAllMyBuckets",
    "s3:GetBucketLocation",
    "eks:ListClusters",
    "eks:DescribeCluster",
    "lambda:ListFunctions",
    "sts:GetCallerIdentity",
]


def build_aws_onboarding_template(
    *,
    trusted_principal_arn: str,
    external_id: str,
) -> dict[str, Any]:
    return {
        "AWSTemplateFormatVersion": "2010-09-09",
        "Description": (
            "Creates the read-only IAM role required by "
            "Alfa Analytics."
        ),
        "Resources": {
            "AlfaAnalyticsReadOnlyRole": {
                "Type": "AWS::IAM::Role",
                "Properties": {
                    "RoleName": "AlfaAnalyticsReadOnlyRole",
                    "Description": (
                        "Read-only inventory role for Alfa Analytics."
                    ),
                    "MaxSessionDuration": 3600,
                    "AssumeRolePolicyDocument": {
                        "Version": "2012-10-17",
                        "Statement": [
                            {
                                "Effect": "Allow",
                                "Principal": {
                                    "AWS": trusted_principal_arn,
                                },
                                "Action": "sts:AssumeRole",
                                "Condition": {
                                    "StringEquals": {
                                        "sts:ExternalId": external_id,
                                    },
                                },
                            },
                        ],
                    },
                    "Policies": [
                        {
                            "PolicyName": (
                                "AlfaAnalyticsInventoryReadOnlyPolicy"
                            ),
                            "PolicyDocument": {
                                "Version": "2012-10-17",
                                "Statement": [
                                    {
                                        "Sid": (
                                            "AlfaAnalyticsInventoryReadOnly"
                                        ),
                                        "Effect": "Allow",
                                        "Action": INVENTORY_READ_ACTIONS,
                                        "Resource": "*",
                                    },
                                ],
                            },
                        },
                    ],
                    "Tags": [
                        {
                            "Key": "ManagedBy",
                            "Value": "AlfaAnalytics",
                        },
                    ],
                },
            },
        },
        "Outputs": {
            "RoleArn": {
                "Description": (
                    "IAM role ARN to register in Alfa Analytics."
                ),
                "Value": {
                    "Fn::GetAtt": [
                        "AlfaAnalyticsReadOnlyRole",
                        "Arn",
                    ],
                },
            },
        },
    }
