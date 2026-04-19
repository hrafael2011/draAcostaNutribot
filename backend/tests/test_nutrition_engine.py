from app.nutrition import compute_nutrition
from app.nutrition.contract import (
    MedicalConditionCode,
    NormalizedActivityLevel,
    NormalizedNutritionGoal,
    NutritionCalculationInput,
    NutritionInput,
    SexForBmr,
)


def _inp(**kwargs) -> NutritionInput:
    defaults = dict(
        weight_kg=70.0,
        height_cm=175.0,
        age_years=30,
        sex=SexForBmr.MALE,
        activity=NormalizedActivityLevel.MODERATE,
        goal=NormalizedNutritionGoal.MAINTENANCE,
        condition_codes=frozenset(),
    )
    defaults.update(kwargs)
    return NutritionInput(calculation=NutritionCalculationInput(**defaults))


def test_bmr_mifflin_male_reference():
    """Hombre 70 kg, 175 cm, 30 a: BMR ≈ 1648.75 (Mifflin–St Jeor)."""
    r = compute_nutrition(_inp()).bmr_kcal
    assert r is not None
    assert abs(r - 1648.75) < 0.1


def test_tdee_maintenance_male():
    r = compute_nutrition(_inp())
    assert r.tdee_kcal is not None and r.activity_factor == 1.55
    assert abs(r.tdee_kcal - 1648.75 * 1.55) < 0.2


def test_bmi_calculation():
    r = compute_nutrition(_inp(weight_kg=80.0, height_cm=180.0))
    # 80 / 1.8^2 ≈ 24.69
    assert r.bmi is not None
    assert abs(r.bmi - 24.69) < 0.05


def test_fat_loss_reduces_calories_vs_maintenance():
    m = compute_nutrition(_inp(goal=NormalizedNutritionGoal.MAINTENANCE))
    f = compute_nutrition(_inp(goal=NormalizedNutritionGoal.FAT_LOSS))
    assert m.target_daily_calories and f.target_daily_calories
    assert f.target_daily_calories < m.target_daily_calories


def test_macros_sum_approximates_target_calories():
    r = compute_nutrition(_inp())
    assert r.target_daily_calories and r.protein_g and r.carbs_g and r.fat_g
    kcal = r.protein_g * 4 + r.carbs_g * 4 + r.fat_g * 9
    assert abs(kcal - r.target_daily_calories) < 8


def test_invalid_weight_blocks():
    r = compute_nutrition(_inp(weight_kg=-1))
    assert r.blocks_generation()


def test_calories_below_floor_blocks():
    # TDEE muy bajo y déficit del 20 % → por debajo del mínimo absoluto femenino
    r = compute_nutrition(
        _inp(
            sex=SexForBmr.FEMALE,
            weight_kg=40.0,
            height_cm=150.0,
            age_years=35,
            activity=NormalizedActivityLevel.SEDENTARY,
            goal=NormalizedNutritionGoal.FAT_LOSS,
        )
    )
    assert r.blocks_generation()
    assert any(a.code == "calories_below_safety_floor" for a in r.alerts)


def test_unspecified_medical_condition_blocks():
    r = compute_nutrition(
        _inp(condition_codes=frozenset({MedicalConditionCode.OTHER_UNSPECIFIED}))
    )
    assert r.blocks_generation()
    assert any(a.code == "condition_unspecified" for a in r.alerts)


def test_bmi_overweight_warns():
    # IMC ≈ 26.1 (sobrepeso, sin llegar a obesidad)
    r = compute_nutrition(_inp(weight_kg=80.0, height_cm=175.0))
    assert any(a.code == "bmi_overweight" for a in r.alerts)


def test_renal_caps_protein_and_sets_rule():
    base = compute_nutrition(
        _inp(goal=NormalizedNutritionGoal.MUSCLE_GAIN, weight_kg=80.0)
    )
    renal = compute_nutrition(
        _inp(
            goal=NormalizedNutritionGoal.MUSCLE_GAIN,
            weight_kg=80.0,
            condition_codes=frozenset({MedicalConditionCode.RENAL}),
        )
    )
    assert base.protein_g and renal.protein_g
    assert renal.protein_g < base.protein_g
    assert "renal_protein_ceiling_applied" in renal.clinical_rules_applied
    assert any(a.code == "renal_protein_policy" for a in renal.alerts)


def test_diabetes_adds_alert_and_rule():
    r = compute_nutrition(
        _inp(condition_codes=frozenset({MedicalConditionCode.DIABETES}))
    )
    assert "diabetes_carb_distribution_low_gi" in r.clinical_rules_applied
    assert any(a.code == "diabetes_meal_planning" for a in r.alerts)


def test_dyslipidemia_reduces_fat_fraction_vs_baseline():
    a = compute_nutrition(_inp(weight_kg=75.0, height_cm=178.0))
    b = compute_nutrition(
        _inp(
            weight_kg=75.0,
            height_cm=178.0,
            condition_codes=frozenset({MedicalConditionCode.DYSLIPIDEMIA}),
        )
    )
    assert a.fat_g and b.fat_g
    assert b.fat_g < a.fat_g
    assert "dyslipidemia_reduced_fat_fraction" in b.clinical_rules_applied


def test_hypertension_adds_sodium_alert():
    r = compute_nutrition(
        _inp(condition_codes=frozenset({MedicalConditionCode.HYPERTENSION}))
    )
    assert any(a.code == "hypertension_sodium" for a in r.alerts)
    assert "hypertension_sodium_moderation" in r.clinical_rules_applied
