"""Motor nutricional determinista: contratos y (próximamente) cálculo."""

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
from app.nutrition.engine import compute_nutrition

__all__ = [
    "ENGINE_SCHEMA_VERSION",
    "MedicalConditionCode",
    "NormalizedActivityLevel",
    "NormalizedNutritionGoal",
    "NutritionAlert",
    "NutritionAlertSeverity",
    "NutritionCalculationInput",
    "NutritionInput",
    "NutritionResult",
    "PatientContextualFactors",
    "SexForBmr",
    "compute_nutrition",
]
