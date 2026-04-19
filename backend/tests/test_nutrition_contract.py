from app.nutrition.contract import (
    ENGINE_SCHEMA_VERSION,
    MedicalConditionCode,
    NormalizedActivityLevel,
    NormalizedNutritionGoal,
    NutritionAlert,
    NutritionAlertSeverity,
    NutritionCalculationInput,
    NutritionInput,
    NutritionResult,
    PatientContextualFactors,
    SexForBmr,
)


def test_nutrition_input_and_result_round_trip_helpers():
    calc = NutritionCalculationInput(
        weight_kg=72.5,
        height_cm=170.0,
        age_years=40,
        sex=SexForBmr.MALE,
        activity=NormalizedActivityLevel.MODERATE,
        goal=NormalizedNutritionGoal.MAINTENANCE,
        condition_codes=frozenset({MedicalConditionCode.DIABETES}),
        food_allergies="cacahuate",
    )
    ctx = PatientContextualFactors(stress_level=3, sleep_hours=6.5)
    inp = NutritionInput(
        calculation=calc,
        contextual=ctx,
        patient_id=99,
        normalization_notes=("activity_level mapped from 'moderate'",),
    )
    assert inp.calculation.weight_kg == 72.5
    assert inp.contextual.stress_level == 3

    alert = NutritionAlert(
        code="demo_block",
        severity=NutritionAlertSeverity.BLOCK,
        message_es="Bloqueo de prueba",
        blocks_generation=True,
    )
    result = NutritionResult(
        engine_schema_version=ENGINE_SCHEMA_VERSION,
        bmr_kcal=1600.0,
        tdee_kcal=2480.0,
        activity_factor=1.55,
        target_daily_calories=2200,
        bmi=25.1,
        protein_g=120.0,
        carbs_g=220.0,
        fat_g=73.0,
        protein_pct=22.0,
        carbs_pct=40.0,
        fat_pct=30.0,
        alerts=(alert,),
        clinical_rules_applied=("diabetes_default",),
    )
    assert result.blocks_generation() is True

    engine = result.to_plan_engine_dict()
    assert engine["engine_schema_version"] == ENGINE_SCHEMA_VERSION
    assert engine["goal_calories"] == 2200

    alerts_json = result.alerts_as_json()
    assert alerts_json[0]["severity"] == "block"
    assert alerts_json[0]["blocks_generation"] is True
