"""PDF de dieta vía plantilla HTML + WeasyPrint (mismo estilo que html_logo)."""

from __future__ import annotations

import base64
from pathlib import Path
from typing import Any, Optional

from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.core.config import settings
from app.models import Diet, Doctor, Patient, PatientMetrics, PatientProfile
from app.services.diet_export import (
    _collect_recommendation_lines,
    _daily_energy_block_lines,
)
from app.services.plan_meals import (
    extract_day_meals,
    meal_slot_label_es,
    normalize_plan_meal_metadata,
    resolve_plan_meal_slots,
)

_TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates"
# backend/app/services -> parents[3] = repo root (diet_telegram_agent)
_REPO_ROOT = Path(__file__).resolve().parents[3]


def _resolve_logo_path() -> Path | None:
    pdf_logo_path = getattr(settings, "PDF_LOGO_PATH", None)
    if pdf_logo_path:
        p = Path(pdf_logo_path).expanduser()
        if p.is_file():
            return p
    nitido = _REPO_ROOT / "html_logo" / "logo_nitido.png"
    if nitido.is_file():
        return nitido
    fallback = Path(__file__).resolve().parent.parent / "assets" / "logo.png"
    if fallback.is_file():
        return fallback
    return None


def _logo_data_uri(path: Path) -> str:
    data = path.read_bytes()
    b64 = base64.standard_b64encode(data).decode("ascii")
    suf = path.suffix.lower()
    mime = "image/png"
    if suf in (".jpg", ".jpeg"):
        mime = "image/jpeg"
    elif suf == ".webp":
        mime = "image/webp"
    return f"data:{mime};base64,{b64}"


def _recommendations_plain(plan: dict[str, Any]) -> str:
    parts = _collect_recommendation_lines(plan)
    return " ".join(parts)


def _html_context(
    diet: Diet,
    *,
    patient: Optional[Patient],
    plan: dict[str, Any],
) -> dict[str, Any]:
    meal_slots = resolve_plan_meal_slots(plan)
    meal_labels = ["Día"] + [meal_slot_label_es(s) for s in meal_slots]
    meal_col_pct = round((100.0 - 3.8) / max(1, len(meal_slots)), 3)

    days_data: list[dict] = []
    if isinstance(plan.get("days"), list):
        days_data = [d for d in plan["days"] if isinstance(d, dict)]

    rows: list[list[str]] = []
    for i in range(1, 8):
        day = next((d for d in days_data if d.get("day") == i), {})
        cells: list[str] = [str(i)]
        for _, _, text in extract_day_meals(day, meal_slots):
            raw = (str(text) if text is not None else "").strip()
            cells.append(raw if raw else "—")
        rows.append(cells)

    first = (patient.first_name or "").strip() if patient else ""
    brand_title = f"Plan Nutricional: {first or 'Paciente'}"

    energy_lines = _daily_energy_block_lines(patient, plan)
    energy_summary = " · ".join(energy_lines) if energy_lines else ""

    logo_path = _resolve_logo_path()
    logo_data_uri = _logo_data_uri(logo_path) if logo_path else None

    return {
        "fecha": diet.created_at.strftime("%d/%m/%Y"),
        "brand_title": brand_title,
        "logo_data_uri": logo_data_uri,
        "meal_slots": meal_slots,
        "meal_labels": meal_labels,
        "meal_col_pct": meal_col_pct,
        "rows": rows,
        "recommendations_text": _recommendations_plain(plan),
        "energy_summary": energy_summary,
    }


def build_diet_export_pdf_bytes_html(
    diet: Diet,
    *,
    patient: Optional[Patient] = None,
    profile: Optional[PatientProfile] = None,
    metrics: Optional[PatientMetrics] = None,
    doctor: Optional[Doctor] = None,
) -> bytes:
    del profile, metrics, doctor
    try:
        from weasyprint import HTML
    except ImportError as e:
        raise RuntimeError("weasyprint not installed") from e

    plan_raw: Any = diet.structured_plan_json or {}
    plan: dict[str, Any] = plan_raw if isinstance(plan_raw, dict) else {}
    plan = normalize_plan_meal_metadata(plan)

    env = Environment(
        loader=FileSystemLoader(str(_TEMPLATE_DIR)),
        autoescape=select_autoescape(["html", "xml", "j2"]),
    )
    template = env.get_template("diet_plan_print.html.j2")
    html_str = template.render(**_html_context(diet, patient=patient, plan=plan))

    base_url = str(_REPO_ROOT.resolve()) + "/"
    return HTML(string=html_str, base_url=base_url).write_pdf()
