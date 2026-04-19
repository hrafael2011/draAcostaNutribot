"""Texto largo de vistas previa de dieta en Telegram (sin estado ni red)."""

from __future__ import annotations

from typing import Optional

from app.models import Diet, Patient
from app.nutrition.plan_display import (
    alerts_text_lines,
    clinical_rules_text_line,
    macro_grams_text_line,
    nutrition_engine_text_lines,
    plan_duration_text_lines,
)
from app.services.plan_meals import (
    extract_day_meals,
    normalize_plan_meal_metadata,
    resolve_plan_meal_slots,
)


def format_diet_preview_message(
    diet: Diet,
    patient: Patient,
    *,
    doctor_note: Optional[str],
) -> str:
    plan = diet.structured_plan_json or {}
    if isinstance(plan, dict):
        plan = normalize_plan_meal_metadata(plan)
    title = plan.get("title") or diet.title or "—"
    lines = [
        f"📋 Vista previa · Dieta #{diet.id} (pendiente de aprobación)",
        f"Paciente: {patient.first_name} {patient.last_name}",
        "",
        f"Título: {title}",
    ]
    summ = (plan.get("summary") or diet.summary or "").strip()
    if summ:
        cut = 480
        lines.append(
            f"Resumen: {summ[:cut]}{'…' if len(summ) > cut else ''}"
        )
    dc = plan.get("daily_calories")
    if dc is not None:
        lines.append(f"Calorías orientativas/día: {dc}")
    if isinstance(plan, dict):
        slots = resolve_plan_meal_slots(plan)
        if slots:
            lines.append(
                f"Comidas por día: {len(slots)} · Estructura: "
                + ", ".join(label for _, label, _ in extract_day_meals({"meals": {}}, slots))
            )
    macros = plan.get("macros")
    if isinstance(macros, dict) and macros:
        lines.append(
            f"Macros: P {macros.get('protein_pct', '—')}% · "
            f"C {macros.get('carbs_pct', '—')}% · "
            f"G {macros.get('fat_pct', '—')}%"
        )
    for dline in plan_duration_text_lines(plan):
        lines.append(dline)
    mg_line = macro_grams_text_line(plan)
    if mg_line:
        lines.append(mg_line)
    ne_lines = nutrition_engine_text_lines(plan)
    if ne_lines:
        lines.append("")
        lines.extend(ne_lines)
    cr = clinical_rules_text_line(plan)
    if cr:
        if len(cr) > 280:
            cr = cr[:277] + "…"
        lines.extend(["", cr])
    alert_lines = alerts_text_lines(plan, max_items=6, max_len=200)
    if alert_lines:
        lines.extend(["", "Alertas / avisos del sistema:"])
        lines.extend(f"• {a}" for a in alert_lines)
    days = plan.get("days")
    if isinstance(days, list) and days:
        d0 = days[0]
        if isinstance(d0, dict):
            lines.extend(["", "Muestra del día 1:"])
            for _, label, raw in extract_day_meals(
                d0,
                resolve_plan_meal_slots(plan if isinstance(plan, dict) else {}),
            ):
                if not raw:
                    continue
                s = str(raw).strip()
                if len(s) > 160:
                    s = s[:157] + "…"
                lines.append(f"• {label}: {s}")
    recs = plan.get("recommendations")
    lines.extend(["", "Recomendaciones clave:"])
    if isinstance(recs, list):
        for item in recs[:5]:
            if isinstance(item, str) and item.strip():
                s = item.strip()
                if len(s) > 190:
                    s = s[:187] + "…"
                lines.append(f"• {s}")
    elif isinstance(recs, str) and recs.strip():
        s = recs.strip()
        lines.append(f"• {s[:400]}{'…' if len(s) > 400 else ''}")
    else:
        lines.append("• (sin bloque de recomendaciones en el plan)")
    if doctor_note and doctor_note.strip():
        note_show = doctor_note.strip()
        if len(note_show) > 140:
            note_show = note_show[:137] + "…"
        lines.extend(
            ["", f"Nota del doctor aplicada: sí — {note_show}"]
        )
    else:
        lines.extend(["", "Nota del doctor aplicada: no"])
    lines.extend(
        [
            "",
            "Revisa el resumen. Si apruebas, envío el PDF final con el detalle completo.",
        ]
    )
    out = "\n".join(lines)
    return out[:4090]
