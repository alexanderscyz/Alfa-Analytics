from app.services.cloudformation import (
    INVENTORY_READ_ACTIONS,
    build_aws_onboarding_template,
)


def test_cloudformation_template_uses_external_id_and_principal() -> None:
    principal_arn = (
        "arn:aws:iam::123456789012:"
        "role/AlfaAnalyticsBackendRole"
    )
    external_id = "11111111-2222-3333-4444-555555555555"

    template = build_aws_onboarding_template(
        trusted_principal_arn=principal_arn,
        external_id=external_id,
    )

    role = template["Resources"]["AlfaAnalyticsReadOnlyRole"]
    properties = role["Properties"]
    trust_statement = properties[
        "AssumeRolePolicyDocument"
    ]["Statement"][0]

    assert role["Type"] == "AWS::IAM::Role"
    assert properties["RoleName"] == "AlfaAnalyticsReadOnlyRole"
    assert trust_statement["Principal"]["AWS"] == principal_arn
    assert (
        trust_statement["Condition"]["StringEquals"][
            "sts:ExternalId"
        ]
        == external_id
    )


def test_cloudformation_template_grants_only_inventory_actions() -> None:
    template = build_aws_onboarding_template(
        trusted_principal_arn=(
            "arn:aws:iam::123456789012:"
            "role/AlfaAnalyticsBackendRole"
        ),
        external_id="example-external-id",
    )

    role = template["Resources"]["AlfaAnalyticsReadOnlyRole"]
    actions = role["Properties"]["Policies"][0][
        "PolicyDocument"
    ]["Statement"][0]["Action"]

    assert actions == INVENTORY_READ_ACTIONS
    assert all(
        action.startswith(
            (
                "ec2:",
                "elasticloadbalancing:",
                "rds:",
                "s3:",
                "eks:",
                "lambda:",
                "sts:",
            )
        )
        for action in actions
    )

    assert "ec2:DescribeNatGateways" in actions
    assert (
        "elasticloadbalancing:DescribeLoadBalancers" in actions
    )
    assert "elasticloadbalancing:DescribeTags" in actions
