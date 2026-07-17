from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.models.cloud_account import CloudAccount
from app.models.cloud_resource import CloudResource
from app.models.finding import Finding


def generate_executive_report(
    account: CloudAccount,
    resources: list[CloudResource],
    findings: list[Finding],
) -> bytes:
    buffer = BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.5 * cm,
        leftMargin=1.5 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
        title=f"Alfa Analytics - {account.name}",
    )

    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="ReportTitle",
            parent=styles["Title"],
            textColor=colors.HexColor("#0891B2"),
            alignment=TA_CENTER,
            spaceAfter=8,
        ),
    )
    styles.add(
        ParagraphStyle(
            name="SectionTitle",
            parent=styles["Heading2"],
            textColor=colors.HexColor("#0F172A"),
            spaceBefore=12,
            spaceAfter=8,
        ),
    )

    total_cost = sum(resource.monthly_cost for resource in resources)
    total_savings = sum(
        finding.estimated_savings for finding in findings
    )

    content = [
        Paragraph("Alfa Analytics", styles["ReportTitle"]),
        Paragraph(
            "Reporte ejecutivo de infraestructura cloud",
            styles["Heading2"],
        ),
        Spacer(1, 12),
        Paragraph(f"<b>Cuenta:</b> {account.name}", styles["BodyText"]),
        Paragraph(
            f"<b>AWS Account ID:</b> {account.aws_account_id}",
            styles["BodyText"],
        ),
        Paragraph(
            f"<b>Estado:</b> {account.status}",
            styles["BodyText"],
        ),
        Spacer(1, 16),
        Paragraph("Resumen ejecutivo", styles["SectionTitle"]),
    ]

    summary_data = [
        ["Indicador", "Resultado"],
        ["Recursos descubiertos", str(len(resources))],
        ["Hallazgos detectados", str(len(findings))],
        ["Costo mensual estimado", f"${total_cost:.2f}"],
        ["Ahorro mensual potencial", f"${total_savings:.2f}"],
    ]

    summary_table = Table(summary_data, colWidths=[10 * cm, 6 * cm])
    summary_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0F172A")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#F8FAFC")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("PADDING", (0, 0), (-1, -1), 8),
            ],
        ),
    )
    content.append(summary_table)

    content.append(Paragraph("Inventario cloud", styles["SectionTitle"]))

    resource_data = [["Servicio", "Recurso", "Region", "Estado", "Costo"]]

    for resource in resources:
        resource_data.append(
            [
                resource.service,
                resource.name,
                resource.region,
                resource.status,
                f"${resource.monthly_cost:.2f}",
            ],
        )

    resource_table = Table(
        resource_data,
        repeatRows=1,
        colWidths=[2.2 * cm, 6 * cm, 2.8 * cm, 2.8 * cm, 2.2 * cm],
    )
    resource_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0891B2")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CBD5E1")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("PADDING", (0, 0), (-1, -1), 6),
            ],
        ),
    )
    content.append(resource_table)

    content.append(
        Paragraph("Hallazgos y recomendaciones", styles["SectionTitle"]),
    )

    for finding in findings:
        content.extend(
            [
                Paragraph(
                    f"<b>{finding.severity.upper()} - "
                    f"{finding.title}</b>",
                    styles["BodyText"],
                ),
                Paragraph(finding.description, styles["BodyText"]),
                Paragraph(
                    f"<b>Recomendacion:</b> {finding.recommendation}",
                    styles["BodyText"],
                ),
                Paragraph(
                    f"<b>Ahorro estimado:</b> "
                    f"${finding.estimated_savings:.2f}/mes",
                    styles["BodyText"],
                ),
                Spacer(1, 10),
            ],
        )

    document.build(content)
    return buffer.getvalue()