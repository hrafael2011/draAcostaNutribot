"""Render a demo diet PDF (new header + logo) to backend/samples/sample_plan.pdf."""

from __future__ import annotations

from datetime import date, datetime, timezone
from pathlib import Path

from app.models import Diet, Patient
from app.services.diet_export import build_diet_export_pdf_bytes


def _demo_plan() -> dict:
    days = []
    for d in range(1, 8):
        days.append(
            {
                "day": d,
                "meals": {
                    "breakfast": "Avena 40 g + leche desnatada 200 ml + fruta",
                    "lunch": "Pollo 120 g + arroz 60 g + ensalada",
                    "snack": "Yogur natural + nueces 15 g",
                    "dinner": "Pescado 130 g + verduras + pan integral 30 g",
                },
            }
        )
    return {
        "daily_calories": 1850,
        "macro_grams": {"protein_g": 95, "carbs_g": 190, "fat_g": 62},
        "meals_per_day": 4,
        "meal_labels": {
            "breakfast": "Desayuno",
            "lunch": "Comida",
            "snack": "Merienda",
            "dinner": "Cena",
        },
        "days": days,
        "recommendations": [
            "Hidratación: 2 L agua/día aprox.",
            "Priorizar alimentos integrales y cocina con poca sal.",
        ],
    }


def main() -> None:
    out_dir = Path(__file__).resolve().parent.parent / "samples"
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / "sample_plan.pdf"
    created = datetime.now(timezone.utc)
    diet = Diet(
        id=999,
        patient_id=1,
        doctor_id=1,
        status="generated",
        title="Plan demostración",
        summary="Plan equilibrado de ejemplo para validar maquetación PDF.",
        structured_plan_json=_demo_plan(),
        notes=None,
        created_at=created,
        updated_at=created,
    )
    patient = Patient(
        id=1,
        doctor_id=1,
        first_name="María",
        last_name="Ejemplo",
        birth_date=date(1988, 3, 20),
    )
    pdf = build_diet_export_pdf_bytes(diet, patient=patient)
    out.write_bytes(pdf)
    print(out)


if __name__ == "__main__":
    main()
