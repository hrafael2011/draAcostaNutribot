import json
import subprocess
from io import BytesIO
from typing import Any, Optional
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.models import Diet, Doctor, Patient, PatientMetrics, PatientProfile
from app.services.diet_export_html import (
    HtmlPdfExportError,
    build_official_diet_export_pdf_bytes,
)
from app.services.doctor_assistant_service import calc_age
from app.services.plan_meals import (
    extract_day_meals,
    normalize_plan_meal_metadata,
    resolve_plan_meal_slots,
)


def _format_daily_calories_line(plan: dict[str, Any]) -> str:
    dc = plan.get("daily_calories")
    if dc is None:
        return "No disponible en este plan."
    try:
        f = float(dc)
    except (TypeError, ValueError):
        return "No disponible en este plan."
    if f != f:  # NaN
        return "No disponible en este plan."
    if f == int(f):
        return f"{int(f)} kcal"
    return f"{round(f, 1)} kcal"


def _macro_grams_line(plan: dict[str, Any]) -> Optional[str]:
    mg = plan.get("macro_grams")
    if not isinstance(mg, dict):
        return None
    pg = _num_str(mg.get("protein_g"))
    cg = _num_str(mg.get("carbs_g"))
    fg = _num_str(mg.get("fat_g"))
    if not (pg and cg and fg):
        return None
    return f"Macronutrientes (referencia diaria): proteínas {pg} g, carbohidratos {cg} g, grasas {fg} g."


def _daily_energy_block_lines(
    patient: Optional[Patient], plan: dict[str, Any]
) -> list[str]:
    lines: list[str] = [f"Calorías diarias: {_format_daily_calories_line(plan)}"]
    macro = _macro_grams_line(plan)
    if macro:
        lines.append(macro)
    if patient and patient.birth_date is not None:
        age = calc_age(patient.birth_date)
        if age is not None:
            lines.append(f"Edad: {age} años")
    return lines


def _daily_energy_inline_line(
    patient: Optional[Patient], plan: dict[str, Any]
) -> str:
    return " · ".join(_daily_energy_block_lines(patient, plan))


def build_diet_export_text(
    diet: Diet, *, patient: Optional[Patient] = None
) -> str:
    plan_raw: Any = diet.structured_plan_json or {}
    plan: dict[str, Any] = plan_raw if isinstance(plan_raw, dict) else {}
    plan = normalize_plan_meal_metadata(plan)

    lines: list[str] = [
        diet.title or "Plan nutricional",
        "=" * 44,
        "",
    ]
    lines.extend(_daily_energy_block_lines(patient, plan))
    lines.extend(["", (diet.summary or "").strip(), ""])
    if isinstance(plan, dict):
        days = plan.get("days")
        if isinstance(days, list):
            for day in days:
                if not isinstance(day, dict):
                    continue
                lines.append(f"--- Día {day.get('day', '?')} ---")
                for _, label, val in extract_day_meals(
                    day,
                    resolve_plan_meal_slots(plan),
                ):
                    if val:
                        lines.append(f"{label}: {val}")
                lines.append("")
        recs = plan.get("recommendations")
        if isinstance(recs, list):
            lines.append("Recomendaciones:")
            for r in recs:
                if isinstance(r, str) and r.strip():
                    lines.append(f"• {r.strip()}")
        elif isinstance(recs, str) and recs.strip():
            lines.append("Recomendaciones:")
            lines.append(recs.strip())
    return "\n".join(lines).strip() + "\n"


def build_diet_export_json_bytes(diet: Diet) -> bytes:
    payload = {
        "id": diet.id,
        "patient_id": diet.patient_id,
        "doctor_id": diet.doctor_id,
        "status": diet.status,
        "title": diet.title,
        "summary": diet.summary,
        "notes": diet.notes,
        "plan": diet.structured_plan_json,
        "created_at": diet.created_at.isoformat(),
        "updated_at": diet.updated_at.isoformat(),
    }
    return json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")


def _xml_para(text: str) -> str:
    if not text:
        return ""
    return escape(str(text)).replace("\n", "<br/>")


def _num_str(v: Any) -> Optional[str]:
    if v is None:
        return None
    try:
        f = float(v)
        if f == int(f):
            return str(int(f))
        return str(round(f, 2))
    except (TypeError, ValueError):
        return str(v)


def _meal_cell_paragraph(text: Any, style: ParagraphStyle) -> Paragraph:
    raw = str(text or "").strip()
    if not raw:
        return Paragraph("—", style)
    return Paragraph(_xml_para(raw), style)


def _collect_recommendation_lines(plan: Any) -> list[str]:
    out: list[str] = []
    if not isinstance(plan, dict):
        return [
            "Consumir entre 8 y 10 vasos de agua al día y dormir de 7 a 8 horas. "
            "Aderezos permitidos: limón, sal y aceite de oliva virgen."
        ]
    plan_recs = plan.get("recommendations")
    if isinstance(plan_recs, str) and plan_recs.strip():
        out.append(plan_recs.strip())
    elif isinstance(plan_recs, list):
        for r in plan_recs:
            if isinstance(r, str) and r.strip():
                out.append(r.strip())
    if not out:
        out.append(
            "Consumir entre 8 y 10 vasos de agua al día y dormir de 7 a 8 horas. "
            "Aderezos permitidos: limón, sal y aceite de oliva virgen."
        )
    return out


def _build_diet_export_pdf_bytes_reportlab(
    diet: Diet,
    *,
    patient: Optional[Patient] = None,
    profile: Optional[PatientProfile] = None,
    metrics: Optional[PatientMetrics] = None,
    doctor: Optional[Doctor] = None,
) -> bytes:
    """PDF para el paciente: encabezado, tabla de comidas con porciones y recomendaciones."""
    buf = BytesIO()
    page_size = landscape(A4)
    doc = SimpleDocTemplate(
        buf,
        pagesize=page_size,
        leftMargin=0.7 * cm,
        rightMargin=0.7 * cm,
        topMargin=0.6 * cm,
        bottomMargin=0.6 * cm,
        title=f"Plan_Nutricional_{(patient.first_name if patient else 'Paciente')}",
    )
    styles = getSampleStyleSheet()
    accent = colors.HexColor("#1e3a5f")
    warm_header = colors.HexColor("#ece7de")
    warm_alt = colors.HexColor("#fcfaf7")
    border = colors.HexColor("#b8b0a1")

    style_meta = ParagraphStyle(
        "Meta",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=10.5,
        textColor=colors.HexColor("#2a2a2a"),
    )
    style_plan_title = ParagraphStyle(
        "PlanTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=13,
        textColor=accent,
        spaceBefore=2,
        spaceAfter=4,
    )
    style_section = ParagraphStyle(
        "Section",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9.5,
        leading=11,
        textColor=accent,
        spaceBefore=5,
        spaceAfter=3,
    )
    style_cell_header = ParagraphStyle(
        "CellHdr",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=10,
        textColor=colors.HexColor("#1b1b1b"),
        alignment=1,
    )
    style_cell_body = ParagraphStyle(
        "CellBody",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7.5,
        leading=9,
        textColor=colors.HexColor("#202020"),
        spaceAfter=0,
    )
    style_rec = ParagraphStyle(
        "RecBullet",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=10.5,
        textColor=colors.HexColor("#303030"),
        leftIndent=10,
        bulletIndent=4,
    )
    style_kcal_inline = ParagraphStyle(
        "KcalInline",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.2,
        leading=10,
        textColor=colors.HexColor("#2a2a2a"),
        alignment=0,
    )

    patient_short_name = "Paciente"
    if patient:
        patient_short_name = (patient.first_name or "Paciente").strip()

    fecha = diet.created_at.strftime("%d/%m/%Y")

    plan: Any = diet.structured_plan_json or {}
    if not isinstance(plan, dict):
        plan = {}
    plan = normalize_plan_meal_metadata(plan)
    meal_slots = resolve_plan_meal_slots(plan)
    compact_meals = len(meal_slots) >= 5
    style_cell_header.fontSize = 8.0 if compact_meals else 8.5
    style_cell_header.leading = 9.2 if compact_meals else 10
    style_cell_body.fontSize = 6.8 if compact_meals else 7.5
    style_cell_body.leading = 8.0 if compact_meals else 9

    story: list[Any] = []

    # ── Encabezado estilo sample ───────────────────────────────────────────
    story.append(Paragraph(f"<b>Fecha:</b> {_xml_para(fecha)}", style_meta))

    # ── Calorías/macros/edad: una sola línea bajo fecha ─
    kcal_line = _daily_energy_inline_line(patient, plan)
    kcal_block = Table(
        [[Paragraph(_xml_para(kcal_line), style_kcal_inline)]],
        colWidths=[doc.width],
    )
    kcal_block.setStyle(
        TableStyle(
            [
                ("LEFTPADDING", (0, 0), (-1, -1), 2),
                ("RIGHTPADDING", (0, 0), (-1, -1), 2),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    story.append(kcal_block)
    story.append(Spacer(1, 0.08 * cm))
    story.append(
        Paragraph(
            f"Plan Nutricional: {_xml_para(patient_short_name)}",
            style_plan_title,
        )
    )
    story.append(Spacer(1, 0.06 * cm))

    # ── Tabla 7 días ─────────────────────────────────────────────────────────

    days_data: list[dict] = []
    if isinstance(plan.get("days"), list):
        days_data = [d for d in plan["days"] if isinstance(d, dict)]

    day_w = 1.0 * cm
    meal_w = (doc.width - day_w) / max(1, len(meal_slots))
    col_widths = [day_w] + [meal_w for _ in meal_slots]

    def pm(markup: str, style: ParagraphStyle) -> Paragraph:
        return Paragraph(markup, style)

    rows: list[list[Any]] = [
        [pm("<b>Día</b>", style_cell_header)]
        + [
            pm(f"<b>{label}</b>", style_cell_header)
            for _, label, _ in extract_day_meals({"meals": {}}, meal_slots)
        ]
    ]
    for i in range(1, 8):
        day = next((d for d in days_data if d.get("day") == i), {})
        rows.append(
            [pm(f"<b>{i}</b>", style_cell_header)]
            + [
                _meal_cell_paragraph(text, style_cell_body)
                for _, _, text in extract_day_meals(day, meal_slots)
            ]
        )

    meal_table = Table(rows, colWidths=col_widths, repeatRows=1)
    meal_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), warm_header),
                ("BACKGROUND", (0, 1), (0, -1), colors.HexColor("#f6f2ea")),
                ("ROWBACKGROUNDS", (1, 1), (-1, -1), [colors.white, warm_alt]),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ALIGN", (0, 0), (0, -1), "CENTER"),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#c7c1b5")),
                ("BOX", (0, 0), (-1, -1), 0.6, border),
                ("LEFTPADDING", (0, 0), (-1, -1), 3 if compact_meals else 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 3 if compact_meals else 4),
                ("TOPPADDING", (0, 0), (-1, -1), 3 if compact_meals else 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3 if compact_meals else 4),
            ]
        )
    )
    story.append(meal_table)
    story.append(Spacer(1, 0.15 * cm))

    # ── Recomendaciones ───────────────────────────────────────────────────────
    story.append(Paragraph("<b>Recomendaciones generales</b>", style_section))
    for rec in _collect_recommendation_lines(plan):
        story.append(Paragraph(f"• {_xml_para(rec)}", style_rec))

    doc.build(story)
    return buf.getvalue()


def build_diet_export_pdf_bytes(
    diet: Diet,
    *,
    patient: Optional[Patient] = None,
    profile: Optional[PatientProfile] = None,
    metrics: Optional[PatientMetrics] = None,
    doctor: Optional[Doctor] = None,
) -> bytes:
    """Official patient PDF.

    The HTML renderer is the source of truth for the polished one-page layout.
    ReportLab remains as a conservative fallback if the browser renderer is not
    available in a test or degraded runtime.
    """
    try:
        return build_official_diet_export_pdf_bytes(diet, patient=patient)
    except (HtmlPdfExportError, OSError, subprocess.SubprocessError):
        return _build_diet_export_pdf_bytes_reportlab(
            diet,
            patient=patient,
            profile=profile,
            metrics=metrics,
            doctor=doctor,
        )
