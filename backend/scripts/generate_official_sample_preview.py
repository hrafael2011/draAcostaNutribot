from __future__ import annotations

import argparse
import asyncio
import sys
from datetime import date
from html import escape
from pathlib import Path
from typing import Any

from sqlalchemy import select

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.core.database import AsyncSessionLocal  # noqa: E402
from app.models import Diet, Patient  # noqa: E402
from app.services.doctor_assistant_service import calc_age  # noqa: E402
from app.services.plan_meals import (  # noqa: E402
    extract_day_meals,
    normalize_plan_meal_metadata,
    resolve_plan_meal_slots,
)


SAMPLES_DIR = ROOT / "samples"


def _num(v: Any) -> str | None:
    if v is None:
        return None
    try:
        f = float(v)
    except (TypeError, ValueError):
        return str(v)
    return str(int(f)) if f == int(f) else str(round(f, 1))


def _energy_line(patient: Patient | None, plan: dict[str, Any]) -> str:
    calories = _num(plan.get("daily_calories")) or "No disponible"
    parts = [f"Calorías diarias: {calories} kcal"]
    macros = plan.get("macro_grams")
    if isinstance(macros, dict):
        protein = _num(macros.get("protein_g"))
        carbs = _num(macros.get("carbs_g"))
        fat = _num(macros.get("fat_g"))
        if protein and carbs and fat:
            parts.append(
                "Macronutrientes (referencia diaria): "
                f"proteínas {protein} g, carbohidratos {carbs} g, grasas {fat} g"
            )
    if patient and patient.birth_date:
        age = calc_age(patient.birth_date)
        if age is not None:
            parts.append(f"Edad: {age} años")
    return " · ".join(parts)


def _recommendations(plan: dict[str, Any]) -> str:
    recs = plan.get("recommendations")
    if isinstance(recs, list):
        lines = [str(item).strip() for item in recs if str(item).strip()]
        if lines:
            return " ".join(lines)
    if isinstance(recs, str) and recs.strip():
        return recs.strip()
    return (
        "Consumir entre 8 y 10 vasos de agua al día y dormir de 7 a 8 horas. "
        "Aderezos permitidos: limón, sal y aceite de oliva virgen."
    )


def _patient_name(patient: Patient | None) -> str:
    if not patient:
        return "Paciente"
    name = " ".join(
        part
        for part in [patient.first_name or "", patient.last_name or ""]
        if part.strip()
    ).strip()
    return name or "Paciente"


def render_html(diet: Diet, patient: Patient | None) -> str:
    plan_raw = diet.structured_plan_json if isinstance(diet.structured_plan_json, dict) else {}
    plan = normalize_plan_meal_metadata(plan_raw)
    slots = resolve_plan_meal_slots(plan)
    days = [day for day in plan.get("days", []) if isinstance(day, dict)][:7]
    while len(days) < 7:
        days.append({"day": len(days) + 1, "meals": {}})

    slot_classes = {
        "breakfast": "breakfast",
        "mid_morning_snack": "snack",
        "lunch": "lunch",
        "snack": "snack",
        "dinner": "dinner",
    }
    col_widths = {
        3: {"breakfast": "30.7%", "lunch": "32.5%", "dinner": "32.0%"},
        4: {"breakfast": "27.6%", "lunch": "27.8%", "snack": "14.4%", "dinner": "26.4%"},
        5: {
            "breakfast": "21.2%",
            "mid_morning_snack": "15.0%",
            "lunch": "24.0%",
            "snack": "14.0%",
            "dinner": "22.0%",
        },
    }.get(len(slots), {})

    name = _patient_name(patient)
    today = date.today().strftime("%d/%m/%Y")
    title = f"Plan Nutricional: {name}"
    energy = _energy_line(patient, plan)

    colgroup = ['<col class="day">']
    for slot in slots:
        width = col_widths.get(slot)
        style = f' style="width: {width}"' if width else ""
        colgroup.append(f'<col class="{slot_classes.get(slot, "meal")}"{style}>')

    headers = ["<th>Día</th>"]
    for _, label, _ in extract_day_meals({"meals": {}}, slots):
        headers.append(f"<th>{escape(label)}</th>")

    rows: list[str] = []
    for idx, day in enumerate(days, start=1):
        cells = [f'<td class="day-cell">{escape(str(day.get("day") or idx))}</td>']
        for _, _, meal in extract_day_meals(day, slots):
            cells.append(f"<td>{escape(meal or '—')}</td>")
        rows.append("<tr>" + "".join(cells) + "</tr>")

    note = escape(_recommendations(plan))

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{escape(title)}</title>
  <style>
    :root {{
      --page-width: 1123px;
      --page-min-height: 794px;
      --content-scale: 0.845;
      --header-purple: #b09fcb;
      --row-purple: #d9d4e5;
      --border: #d1ccd8;
      --note-bg: #eef0fa;
      --note-accent: #7d91c1;
      --note-title: #50628e;
      --text: #181818;
    }}

    * {{ box-sizing: border-box; }}

    @page {{ size: A4 landscape; margin: 0; }}

    html, body {{
      margin: 0;
      padding: 0;
      background: #ffffff;
      color: var(--text);
      font-family: Arial, Helvetica, sans-serif;
      -webkit-print-color-adjust: exact;
      print-color-adjust: exact;
    }}

    body {{ display: flex; justify-content: center; }}

    .page {{
      width: 100%;
      max-width: var(--page-width);
      min-height: var(--page-min-height);
      padding: 8px 12px 5px;
      overflow: hidden;
    }}

    .page-inner {{
      width: calc(100% / var(--content-scale));
      transform: scale(var(--content-scale));
      transform-origin: top left;
    }}

    .top-meta {{
      display: flex;
      justify-content: flex-end;
      align-items: center;
      margin-bottom: 3px;
      padding-right: 14px;
      font-size: 15px;
      font-weight: 700;
      color: #111111;
    }}

    .brand {{
      display: flex;
      justify-content: center;
      align-items: center;
      gap: 28px;
      margin: 2px 0 5px;
    }}

    .brand-logo {{
      width: 142px;
      height: auto;
      display: block;
      object-fit: contain;
      image-rendering: auto;
      filter: contrast(1.08) saturate(1.05);
    }}

    .brand-title {{
      margin: 0;
      font-size: 22px;
      font-weight: 700;
      color: #0b0b0b;
    }}

    .energy-line {{
      max-width: 920px;
      margin: 0 auto 10px;
      text-align: center;
      font-size: 14px;
      line-height: 1.25;
      font-weight: 700;
      color: #111111;
    }}

    table {{
      width: 100%;
      border-collapse: collapse;
      table-layout: fixed;
    }}

    col.day {{ width: 3.8%; }}

    thead th {{
      padding: 8px 8px;
      border: 1px solid var(--border);
      background: var(--header-purple);
      color: #ffffff;
      font-size: 18px;
      font-weight: 700;
      text-align: center;
    }}

    tbody td {{
      padding: 10.5px 16px;
      border: 1px solid var(--border);
      font-size: 14.8px;
      line-height: 1.42;
      vertical-align: top;
      text-align: justify;
      text-justify: inter-word;
      word-break: normal;
    }}

    tbody tr:nth-child(even) td {{ background: var(--row-purple); }}

    td.day-cell {{
      padding: 12px 8px;
      font-size: 13px;
      text-align: center;
      vertical-align: middle;
    }}

    .note {{
      margin-top: 10px;
      border-left: 8px solid var(--note-accent);
      background: var(--note-bg);
      padding: 13px 18px;
      font-size: 16px;
      line-height: 1.28;
      color: #343434;
    }}

    .note strong {{ color: var(--note-title); }}
  </style>
</head>
<body>
  <main class="page">
    <div class="page-inner">
      <div class="top-meta">Fecha: {today}</div>
      <section class="brand" aria-label="Encabezado del plan nutricional">
        <img class="brand-logo" src="html_logo/logo_nitido.png" alt="Logo Dra. Acosta Fit">
        <h1 class="brand-title">{escape(title)}</h1>
      </section>
      <div class="energy-line">{escape(energy)}</div>
      <table aria-label="Plan nutricional semanal">
        <colgroup>
          {"".join(colgroup)}
        </colgroup>
        <thead><tr>{"".join(headers)}</tr></thead>
        <tbody>{"".join(rows)}</tbody>
      </table>
      <section class="note"><strong>Recomendaciones:</strong> {note}</section>
    </div>
  </main>
</body>
</html>
"""


async def load_diet(diet_id: int | None) -> tuple[Diet, Patient | None]:
    async with AsyncSessionLocal() as session:
        stmt = select(Diet)
        if diet_id is not None:
            stmt = stmt.where(Diet.id == diet_id)
        stmt = stmt.order_by(Diet.id.desc()).limit(1)
        diet = (await session.execute(stmt)).scalar_one()
        patient = (
            await session.execute(select(Patient).where(Patient.id == diet.patient_id))
        ).scalar_one_or_none()
        return diet, patient


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--diet-id", type=int, default=None)
    parser.add_argument(
        "--output",
        type=Path,
        default=SAMPLES_DIR / "sample_plan_official_preview.html",
    )
    args = parser.parse_args()

    diet, patient = await load_diet(args.diet_id)
    html = render_html(diet, patient)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(html, encoding="utf-8")
    print(args.output)


if __name__ == "__main__":
    asyncio.run(main())
