from app.services.plan_meals import (
    extract_day_meals,
    normalize_plan_meal_metadata,
    resolve_plan_meal_slots,
)


def test_normalize_legacy_plan_defaults_to_four_slots():
    plan = {
        "days": [
            {
                "day": 1,
                "breakfast": "Avena",
                "lunch": "Pollo",
                "snack": "Yogur",
                "dinner": "Sopa",
            }
        ]
    }
    out = normalize_plan_meal_metadata(plan)
    assert out["meals_per_day"] == 4
    assert out["meal_slots"] == ["breakfast", "lunch", "snack", "dinner"]
    assert out["days"][0]["meals"]["snack"] == "Yogur"


def test_normalize_new_plan_uses_requested_meal_slots():
    plan = {
        "days": [
            {
                "day": 1,
                "meals": {
                    "breakfast": "Huevos",
                    "mid_morning_snack": "Fruta",
                    "lunch": "Arroz",
                    "snack": "Yogur",
                    "dinner": "Pescado",
                },
            }
        ]
    }
    out = normalize_plan_meal_metadata(plan, requested_meals_per_day=5)
    assert out["meals_per_day"] == 5
    assert resolve_plan_meal_slots(out) == [
        "breakfast",
        "mid_morning_snack",
        "lunch",
        "snack",
        "dinner",
    ]
    labels = [label for _, label, _ in extract_day_meals(out["days"][0], out["meal_slots"])]
    assert labels[1] == "Media mañana"
