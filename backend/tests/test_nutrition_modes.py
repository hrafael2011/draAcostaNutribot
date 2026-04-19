"""Modos auto / guiado / manual del motor nutricional."""

from datetime import date

from app.models import Patient, PatientMetrics, PatientProfile, utcnow
from app.nutrition import compute_nutrition
from app.nutrition.contract import NutritionStrategyMode
from app.nutrition.input_builder import build_nutrition_input_from_bundle
from app.nutrition.plan_merge import merge_nutrition_into_plan


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
        activity_level="moderate",
    )
    m = PatientMetrics(
        patient_id=1,
        weight_kg=80,
        height_cm=180,
        recorded_at=utcnow(),
    )
    return p, pr, m


def test_guided_low_carb_reduces_carbs_vs_auto():
    p, pr, m = _bundle()
    auto_in = build_nutrition_input_from_bundle(p, pr, m, strategy_mode="auto")
    guided_in = build_nutrition_input_from_bundle(
        p,
        pr,
        m,
        strategy_mode="guided",
        diet_style="low_carb",
    )
    auto_out = compute_nutrition(auto_in)
    guided_out = compute_nutrition(guided_in)
    assert auto_out.carbs_g and guided_out.carbs_g
    assert guided_out.carbs_g < auto_out.carbs_g
    assert guided_out.applied_mode == NutritionStrategyMode.GUIDED


def test_manual_daily_calories_override():
    p, pr, m = _bundle()
    n_in = build_nutrition_input_from_bundle(
        p,
        pr,
        m,
        strategy_mode="manual",
        manual_targets={"daily_calories": 1650},
    )
    r = compute_nutrition(n_in)
    assert not r.blocks_generation()
    assert r.target_daily_calories == 1650
    assert r.manual_override_used is True
    assert r.applied_mode == NutritionStrategyMode.MANUAL


def test_manual_below_floor_warns_not_blocks():
    p, pr, m = _bundle()
    n_in = build_nutrition_input_from_bundle(
        p,
        pr,
        m,
        strategy_mode="manual",
        manual_targets={"daily_calories": 1000},
    )
    r = compute_nutrition(n_in)
    assert not r.blocks_generation()
    assert any(a.code == "manual_calories_below_safety_floor" for a in r.alerts)


def test_merge_includes_strategy_metadata():
    p, pr, m = _bundle()
    n_in = build_nutrition_input_from_bundle(
        p,
        pr,
        m,
        strategy_mode="manual",
        manual_targets={"daily_calories": 1700, "protein_g": 120},
    )
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
    assert merged["applied_mode"] == "manual"
    assert merged["manual_override_used"] is True
    assert "applied_preferences" in merged
