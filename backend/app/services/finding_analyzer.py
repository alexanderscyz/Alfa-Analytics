from decimal import Decimal

from app.models.cloud_resource import CloudResource
from app.models.finding import Finding


def analyze_resources(
    resources: list[CloudResource],
) -> list[Finding]:
    findings: list[Finding] = []

    for resource in resources:
        if resource.service == "EC2" and resource.status == "stopped":
            findings.append(
                Finding(
                    cloud_account_id=resource.cloud_account_id,
                    cloud_resource_id=resource.id,
                    category="cost",
                    severity="high",
                    title="EC2 detenida generando costos",
                    description=(
                        f"La instancia {resource.name} está detenida, "
                        "pero mantiene costos asociados."
                    ),
                    recommendation=(
                        "Validar si la instancia todavía es necesaria y "
                        "eliminar sus recursos asociados si está fuera de uso."
                    ),
                    estimated_savings=resource.monthly_cost,
                ),
            )

        if (
            resource.service == "EBS"
            and resource.resource_metadata.get("size_gb", 0) >= 200
        ):
            findings.append(
                Finding(
                    cloud_account_id=resource.cloud_account_id,
                    cloud_resource_id=resource.id,
                    category="optimization",
                    severity="medium",
                    title="Volumen EBS requiere revisión",
                    description=(
                        f"El volumen {resource.name} tiene "
                        f"{resource.resource_metadata['size_gb']} GB."
                    ),
                    recommendation=(
                        "Revisar el uso real del volumen y reducir su tamaño "
                        "si existe capacidad sin utilizar."
                    ),
                    estimated_savings=(
                        resource.monthly_cost * Decimal("0.30")
                    ),
                ),
            )

        if (
            resource.service == "RDS"
            and resource.monthly_cost > Decimal("100")
        ):
            findings.append(
                Finding(
                    cloud_account_id=resource.cloud_account_id,
                    cloud_resource_id=resource.id,
                    category="cost",
                    severity="medium",
                    title="Instancia RDS con costo elevado",
                    description=(
                        f"La base de datos {resource.name} tiene un costo "
                        f"estimado de ${resource.monthly_cost} mensuales."
                    ),
                    recommendation=(
                        "Revisar utilización, tamaño de instancia y opciones "
                        "de reserva o Savings Plans aplicables."
                    ),
                    estimated_savings=(
                        resource.monthly_cost * Decimal("0.20")
                    ),
                ),
            )

        if (
            resource.service == "S3"
            and not resource.resource_metadata.get("versioning")
        ):
            findings.append(
                Finding(
                    cloud_account_id=resource.cloud_account_id,
                    cloud_resource_id=resource.id,
                    category="risk",
                    severity="medium",
                    title="Bucket S3 sin versionado",
                    description=(
                        f"El bucket {resource.name} no tiene versionado "
                        "registrado."
                    ),
                    recommendation=(
                        "Habilitar versionado para reducir el riesgo de "
                        "pérdida o eliminación accidental de objetos."
                    ),
                    estimated_savings=Decimal("0"),
                ),
            )

    return findings