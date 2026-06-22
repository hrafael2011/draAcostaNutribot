"""Genera PDF de ejemplo del entregable (plantilla malva) en example/."""

from __future__ import annotations

from datetime import date, datetime, timezone
from pathlib import Path

from app.models import Diet, Patient
from app.services.diet_export import build_diet_export_pdf_bytes


def _rich_demo_plan() -> dict:
    """Contenido tipo plantilla html_logo (7 días, 4 comidas)."""
    days_data = [
        (
            1,
            "2 huevos revueltos (140g) con espinacas salteadas (100g) y 1 rebanada de pan integral tostado (30g), cocido en 1 cucharadita de aceite de oliva.",
            "150g de pechuga de pollo a la plancha con 200g de brócoli al vapor y 100g de quinoa cocida, aderezado con limón y pimienta.",
            "1 manzana mediana (150g) y 30g de almendras.",
            "200g de pavo molido salteado con 1 taza de pimientos asados (150g) y 1 taza de arroz integral cocido (150g).",
        ),
        (
            2,
            "1 taza de yogur natural (240g) con 100g de fresas y 30g de granola sin azúcar.",
            "Ensalada de 150g de pechuga de pavo, 100g de espinacas, 50g de aguacate, 50g de tomates cherry y 1 cucharada de aceite de oliva.",
            "1 plátano (120g) y 2 cucharadas de mantequilla de almendra.",
            "200g de pollo al horno con especias, 150g de batatas asadas y 100g de judías verdes al vapor.",
        ),
        (
            3,
            "Smoothie de 1 plátano (120g), 1 taza de leche de almendra (240ml)",
            "Wrap de 150g de pechuga de pollo en tortilla integral (60g) con lechuga, tomate y 30g de hummus.",
            "1 pera mediana (150g) y 15g de nueces.",
            "200g de carne magra de res a la parrilla con 150g de calabacín asado y 100g de arroz basmati cocido.",
        ),
        (
            4,
            "3 claras de huevo (100g) con 50g de champiñones salteados y 1 rebanada de pan integral (30g).",
            "150g de pollo al curry con 200g de coliflor al vapor y 100g de cuscús.",
            "1 naranja mediana (130g) y 30g de semillas de girasol.",
            "200g de pavo al horno con 150g de zanahorias asadas y 100g de puré de patatas.",
        ),
        (
            5,
            "1 taza de avena cocida (240ml) con 1 cucharada de miel y 30g de arándanos.",
            "Sopa de 200g de lentejas con verduras (zanahorias, apio, cebolla) y 50g de pan integral.",
            "1 batido de 240ml de leche de almendra con fresa y 1 plátano (120g).",
            "200g de pollo a la parrilla con 100g de espárragos y 100g de arroz integral.",
        ),
        (
            6,
            "2 tortillas integrales (60g) con 2 huevos revueltos (140g) y 50g de aguacate.",
            "Ensalada de 150g de pollo a la parrilla, 100g de lechuga, 50g de zanahoria rallada y 1 cucharada de aderezo de yogur.",
            "1 manzana (150g) y 30g de nueces.",
            "200g de carne magra de res al horno con 200g de espinacas salteadas en 1 cucharadita de aceite de oliva.",
        ),
        (
            7,
            "1 taza de yogur griego (240g) con 100g de mango y 30g de semillas de chía.",
            "150g de pechuga de pavo en rodajas con 100g de espárragos y 100g de quinoa.",
            "1 plátano (120g) y 2 cucharadas de mantequilla de almendra.",
            "200g de pollo al horno con 150g de brócoli y 100g de arroz integral.",
        ),
    ]
    days = []
    for d, breakfast, lunch, snack, dinner in days_data:
        days.append(
            {
                "day": d,
                "meals": {
                    "breakfast": breakfast,
                    "lunch": lunch,
                    "snack": snack,
                    "dinner": dinner,
                },
            }
        )
    return {
        "daily_calories": 1950,
        "macro_grams": {"protein_g": 98, "carbs_g": 195, "fat_g": 58},
        "meals_per_day": 4,
        "days": days,
        "recommendations": [
            "Consumir mínimo entre 8 a 10 vasos de agua y dormir de 7 a 8 horas al día; "
            "aderezos: limón, sal y aceite de oliva virgen.",
        ],
    }


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    out_dir = repo_root / "example"
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / "plan_nutricional_entregable_ejemplo.pdf"
    created = datetime(2025, 10, 26, 12, 0, 0, tzinfo=timezone.utc)
    diet = Diet(
        id=0,
        patient_id=1,
        doctor_id=1,
        status="generated",
        title="Plan nutricional ejemplo",
        summary="Documento de demostración del formato de entregable.",
        structured_plan_json=_rich_demo_plan(),
        notes=None,
        created_at=created,
        updated_at=created,
    )
    patient = Patient(
        id=1,
        doctor_id=1,
        first_name="Kevin",
        last_name="Ejemplo",
        birth_date=date(1992, 5, 10),
    )
    pdf = build_diet_export_pdf_bytes(diet, patient=patient)
    out.write_bytes(pdf)
    print(out.resolve())
    print(f"OK {len(pdf)} bytes")


if __name__ == "__main__":
    main()
