"""Export PDF/TXT: bloque de calorías, privacidad (nota del doctor y perfil clínico)."""

from __future__ import annotations

import re
from datetime import date, datetime, timezone
from io import BytesIO

from pypdf import PdfReader

from app.models import Diet, Patient, PatientProfile
from app.services.diet_export import build_diet_export_pdf_bytes, build_diet_export_text


def _pdf_extract_text(pdf_bytes: bytes) -> str:
    reader = PdfReader(BytesIO(pdf_bytes))
    return "".join((p.extract_text() or "") for p in reader.pages)


def _minimal_plan() -> dict:
    return {
        "daily_calories": 1800,
        "macro_grams": {"protein_g": 90, "carbs_g": 200, "fat_g": 60},
        "days": [
            {
                "day": 1,
                "breakfast": "Ejemplo",
                "lunch": "",
                "snack": "",
                "dinner": "",
            }
        ],
        "recommendations": ["Beber agua."],
    }


def test_pdf_contains_kcal_hides_doctor_note_and_profile_diseases():
    created = datetime(2026, 4, 1, 12, 0, 0, tzinfo=timezone.utc)
    diet = Diet(
        id=1,
        patient_id=1,
        doctor_id=1,
        status="generated",
        title="Plan demo",
        summary="Resumen corto.",
        structured_plan_json=_minimal_plan(),
        notes="DOCTOR_SECRET_NOTE_UNIQUE_99",
        created_at=created,
        updated_at=created,
    )
    patient = Patient(
        id=1,
        doctor_id=1,
        first_name="Ana",
        last_name="García",
        birth_date=date(1990, 6, 15),
    )
    profile = PatientProfile(
        id=1,
        patient_id=1,
        diseases="CONDICION_PRIVADA_NO_PDF_12345",
    )
    pdf = build_diet_export_pdf_bytes(diet, patient=patient, profile=profile)
    text = _pdf_extract_text(pdf)
    assert "1800" in text
    assert "DOCTOR_SECRET" not in text
    assert "CONDICION_PRIVADA" not in text


def test_text_export_kcal_age_macros_hides_note():
    created = datetime(2026, 4, 1, 12, 0, 0, tzinfo=timezone.utc)
    diet = Diet(
        id=2,
        patient_id=1,
        doctor_id=1,
        status="generated",
        title="Plan demo",
        summary="Resumen.",
        structured_plan_json=_minimal_plan(),
        notes="NOTA_OCULTA_XYZ",
        created_at=created,
        updated_at=created,
    )
    patient = Patient(
        id=1,
        doctor_id=1,
        first_name="Ana",
        last_name="García",
        birth_date=date(1990, 6, 15),
    )
    txt = build_diet_export_text(diet, patient=patient)
    assert "Calorías diarias" in txt
    assert "Macronutrientes (referencia diaria)" in txt
    assert "1800 kcal" in txt
    assert "proteínas 90 g" in txt
    assert re.search(r"Edad: \d+ años", txt)
    assert "NOTA_OCULTA" not in txt
    assert "Modo de objetivos" not in txt
    assert "Objetivo energético diario estimado" not in txt
    assert "Información orientativa" not in txt


def test_text_when_daily_calories_missing():
    created = datetime(2026, 4, 1, 12, 0, 0, tzinfo=timezone.utc)
    plan = _minimal_plan()
    del plan["daily_calories"]
    diet = Diet(
        id=3,
        patient_id=1,
        doctor_id=1,
        status="generated",
        title="Plan",
        summary="S.",
        structured_plan_json=plan,
        notes=None,
        created_at=created,
        updated_at=created,
    )
    txt = build_diet_export_text(diet, patient=None)
    assert "No disponible en este plan." in txt


def test_pdf_compacts_five_meals_and_hides_system_metadata():
    created = datetime(2026, 4, 1, 12, 0, 0, tzinfo=timezone.utc)
    plan = {
        "daily_calories": 1500,
        "macro_grams": {"protein_g": 122.2, "carbs_g": 147.7, "fat_g": 46.7},
        "meals_per_day": 5,
        "meal_slots": [
            "breakfast",
            "mid_morning_snack",
            "lunch",
            "snack",
            "dinner",
        ],
        "applied_mode": "manual",
        "manual_override_used": True,
        "days": [
            {
                "day": 1,
                "meals": {
                    "breakfast": "Avena",
                    "mid_morning_snack": "Fruta",
                    "lunch": "Pollo con arroz",
                    "snack": "Yogur",
                    "dinner": "Pescado",
                },
            }
        ],
        "recommendations": ["Beber agua."],
    }
    diet = Diet(
        id=4,
        patient_id=1,
        doctor_id=1,
        status="generated",
        title="Plan demo 5 comidas",
        summary="Resumen.",
        structured_plan_json=plan,
        notes=None,
        created_at=created,
        updated_at=created,
    )
    patient = Patient(
        id=1,
        doctor_id=1,
        first_name="Ana",
        last_name="García",
        birth_date=date(1990, 6, 15),
    )
    pdf = build_diet_export_pdf_bytes(diet, patient=patient)
    text = _pdf_extract_text(pdf)
    assert "Media mañana" in text
    assert "Merienda" in text
    assert "Modo de objetivos" not in text
    assert "manual" not in text.lower()
