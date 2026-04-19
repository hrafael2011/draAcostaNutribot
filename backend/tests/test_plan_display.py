from app.nutrition.plan_display import (
    alerts_text_lines,
    clinical_rules_text_line,
    macro_grams_text_line,
    nutrition_engine_text_lines,
)


def test_plan_display_empty_legacy():
    assert nutrition_engine_text_lines({}) == []
    assert macro_grams_text_line({}) is None
    assert clinical_rules_text_line({}) is None
    assert alerts_text_lines({}) == []


def test_plan_display_with_engine():
    plan = {
        "nutrition_engine": {
            "engine_schema_version": "1.0",
            "bmr_kcal": 1500.0,
            "tdee_kcal": 2300.0,
            "bmi": 24.5,
            "activity_factor": 1.55,
            "goal_calories": 2100,
        },
        "macro_grams": {"protein_g": 100, "carbs_g": 200, "fat_g": 70},
        "clinical_rules_applied": ["diabetes_carb_distribution_low_gi"],
        "alerts": [
            {"severity": "warn", "message_es": "Prueba"},
        ],
    }
    assert any("TMB" in L for L in nutrition_engine_text_lines(plan))
    assert "proteína" in (macro_grams_text_line(plan) or "")
    assert "diabetes" in (clinical_rules_text_line(plan) or "")
    assert alerts_text_lines(plan)[0].startswith("[WARN]")


def test_plan_display_shows_guided_mode_and_warnings():
    plan = {
        "nutrition_engine": {
            "engine_schema_version": "1.0",
            "bmr_kcal": 1500.0,
            "tdee_kcal": 2300.0,
            "goal_calories": 1900,
            "applied_mode": "guided",
            "manual_override_used": False,
            "override_warnings": ["Aviso de prueba para el profesional."],
        },
    }
    lines = nutrition_engine_text_lines(plan)
    assert any("Modo de objetivos: guided" in L for L in lines)
    assert any("Aviso:" in L for L in lines)
