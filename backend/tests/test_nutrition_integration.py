import asyncio
from datetime import date

from app.models import Patient, PatientMetrics, PatientProfile, utcnow
from app.nutrition import compute_nutrition
from app.nutrition.contract import NormalizedActivityLevel, NormalizedNutritionGoal
from app.nutrition.input_builder import build_nutrition_input_from_bundle
from app.nutrition.plan_merge import merge_nutrition_into_plan
from app.services import diet_service
from app.services.diet_service import _generate_plan_with_nutrition_engine


def _bundle():
    p = Patient(
        doctor_id=1,
        first_name="A",
        last_name="B",
        birth_date=date(1990, 1, 1),
        sex="male",
        country="DR",
        city="SD",
    )
    p.id = 1
    pr = PatientProfile(
        patient_id=1,
        objective="lose_weight",
        food_allergies="none",
        foods_avoided="none",
        activity_level="low",
    )
    m = PatientMetrics(
        patient_id=1,
        weight_kg=80,
        height_cm=180,
        recorded_at=utcnow(),
    )
    return p, pr, m


def test_input_builder_objective_and_activity():
    p, pr, m = _bundle()
    n_in = build_nutrition_input_from_bundle(p, pr, m)
    assert n_in.calculation.goal == NormalizedNutritionGoal.FAT_LOSS
    assert n_in.calculation.activity == NormalizedActivityLevel.LIGHT
    n_out = compute_nutrition(n_in)
    assert not n_out.blocks_generation()
    assert n_out.target_daily_calories


def test_merge_overwrites_llm_numbers_and_adds_engine():
    p, pr, m = _bundle()
    n_in = build_nutrition_input_from_bundle(p, pr, m)
    n_out = compute_nutrition(n_in)
    plan = {
        "title": "t",
        "summary": "s",
        "daily_calories": 9999,
        "macros": {"protein_pct": 5, "carbs_pct": 5, "fat_pct": 5},
        "days": [],
        "recommendations": [],
    }
    merged = merge_nutrition_into_plan(plan, n_out, nutrition_input=n_in)
    assert merged["daily_calories"] == n_out.target_daily_calories
    assert merged["macros"]["protein_pct"] == n_out.protein_pct
    assert "nutrition_engine" in merged
    assert "contextual_factors" in merged


def test_generate_plan_with_engine_uses_targets_and_merge(monkeypatch):
    async def fake_gen(snapshot, instruction, nutrition_targets=None):
        assert nutrition_targets is not None
        assert nutrition_targets["authoritative"] is True
        assert nutrition_targets["daily_calories"] is not None
        assert instruction == "nota"
        return {
            "title": "t",
            "summary": "s",
            "daily_calories": 9999,
            "macros": {"protein_pct": 5, "carbs_pct": 5, "fat_pct": 5},
            "days": [
                {
                    "day": d,
                    "breakfast": "a",
                    "lunch": "b",
                    "snack": "c",
                    "dinner": "d",
                }
                for d in range(1, 8)
            ],
            "recommendations": ["r1", "r2", "r3", "r4"],
        }

    monkeypatch.setattr(diet_service, "generate_diet_plan_json", fake_gen)
    p, pr, m = _bundle()

    async def run():
        return await _generate_plan_with_nutrition_engine(
            p, pr, m, "nota", duration_days=21
        )

    snap, plan = asyncio.run(run())
    assert snap["patient"]["first_name"] == "A"
    assert plan["daily_calories"] != 9999
    assert plan["nutrition_engine"]["goal_calories"] == plan["daily_calories"]
    assert plan.get("plan_duration_days") == 21
