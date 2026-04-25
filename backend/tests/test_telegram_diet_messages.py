from datetime import date

import pytest

from app.models import Diet, Patient
from app.services.telegram_diet_messages import (
    format_diet_preview_message,
    format_telegram_full_day_block,
    split_telegram_text_chunks,
)


def test_format_diet_preview_includes_title_and_patient():
    p = Patient(
        doctor_id=1,
        first_name="Ana",
        last_name="López",
        birth_date=date(1990, 1, 1),
        sex="female",
        country="ES",
        city="Madrid",
    )
    p.id = 3
    d = Diet(
        patient_id=3,
        doctor_id=1,
        status="pending_approval",
        title="Plan",
        summary="Resumen corto",
        structured_plan_json={
            "title": "Plan JSON",
            "daily_calories": 1800,
            "days": [{"day": 1, "breakfast": "x"}],
            "recommendations": ["Beber agua"],
        },
        notes=None,
    )
    d.id = 99
    text = format_diet_preview_message(d, p, doctor_note=None)
    assert "Dieta #99" in text
    assert "Ana" in text and "López" in text
    assert "Plan JSON" in text or "Plan" in text


@pytest.mark.parametrize(
    ("meals_per_day", "meal_slots", "expected_tokens"),
    [
        (2, ["breakfast", "dinner"], ["Comidas por día: 2", "Desayuno", "Cena"]),
        (3, ["breakfast", "lunch", "dinner"], ["Comidas por día: 3", "Desayuno", "Comida", "Cena"]),
        (4, ["breakfast", "lunch", "snack", "dinner"], ["Comidas por día: 4", "Merienda"]),
        (
            5,
            ["breakfast", "mid_morning_snack", "lunch", "snack", "dinner"],
            ["Comidas por día: 5", "Media mañana", "Merienda"],
        ),
    ],
)
def test_format_diet_preview_shows_expected_meal_structure(
    meals_per_day: int,
    meal_slots: list[str],
    expected_tokens: list[str],
):
    p = Patient(
        doctor_id=1,
        first_name="Ana",
        last_name="López",
        birth_date=date(1990, 1, 1),
        sex="female",
        country="ES",
        city="Madrid",
    )
    p.id = 3
    d = Diet(
        patient_id=3,
        doctor_id=1,
        status="pending_approval",
        title="Plan 5 comidas",
        summary="Resumen corto",
        structured_plan_json={
            "title": "Plan JSON",
            "daily_calories": 1800,
            "meals_per_day": meals_per_day,
            "meal_slots": meal_slots,
            "days": [
                {
                    "day": 1,
                    "meals": {slot: f"Meal {slot}" for slot in meal_slots},
                }
            ],
            "recommendations": ["Beber agua"],
        },
        notes=None,
    )
    d.id = 101
    text = format_diet_preview_message(d, p, doctor_note=None)
    assert "Muestra del día 1:" in text
    for token in expected_tokens:
        assert token in text


def test_split_telegram_text_chunks_respects_max_len():
    s = "x" * 10000
    parts = split_telegram_text_chunks(s, 4000)
    assert all(len(p) <= 4000 for p in parts)
    assert "".join(parts) == s


def test_format_telegram_full_day_block_shows_slotted_meals():
    plan = {
        "meals_per_day": 2,
        "meal_slots": ["breakfast", "dinner"],
        "days": [
            {
                "day": 1,
                "date": "2026-01-01",
                "meals": {
                    "breakfast": "Tostada",
                    "dinner": "Pescado",
                },
            }
        ],
    }
    out = format_telegram_full_day_block(plan, 0, num_days=1)
    assert "Día 1" in out
    assert "Tostada" in out
    assert "Pescado" in out
