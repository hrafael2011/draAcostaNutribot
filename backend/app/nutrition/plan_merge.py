"""Integra la salida del motor en structured_plan_json y payload para el LLM."""

from __future__ import annotations

from dataclasses import fields
from typing import Any, Optional

from app.nutrition.contract import NutritionInput, NutritionResult


def nutrition_targets_for_llm(result: NutritionResult) -> dict[str, Any]:
    """Objeto que recibe el modelo: cifras oficiales + alertas para redacción del menú."""
    return {
        "authoritative": True,
        "instruction_es": (
            "Estos valores son la fuente oficial del sistema. En tu JSON de salida debes "
            "usar EXACTAMENTE el mismo daily_calories y el mismo objeto macros "
            "(protein_pct, carbs_pct, fat_pct) que aquí. No recalcules ni redondees distinto. "
            "Tu trabajo es redactar comidas y recomendaciones coherentes con esos objetivos."
        ),
        "daily_calories": result.target_daily_calories,
        "macros": {
            "protein_pct": result.protein_pct,
            "carbs_pct": result.carbs_pct,
            "fat_pct": result.fat_pct,
        },
        "macro_grams": {
            "protein_g": result.protein_g,
            "carbs_g": result.carbs_g,
            "fat_g": result.fat_g,
        },
        "nutrition_engine": result.to_plan_engine_dict(),
        "alerts": result.alerts_as_json(),
        "clinical_rules_applied": list(result.clinical_rules_applied),
    }


def _contextual_to_dict(ctx: Any) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for f in fields(ctx):
        v = getattr(ctx, f.name)
        if v is None:
            continue
        if isinstance(v, str) and not v.strip():
            continue
        out[f.name] = v
    return out


def merge_nutrition_into_plan(
    plan: dict[str, Any],
    nutrition_result: NutritionResult,
    *,
    nutrition_input: Optional[NutritionInput] = None,
) -> dict[str, Any]:
    """Enriquece el JSON del plan con el motor; sobrescribe calorías y macros del LLM."""
    out = dict(plan)
    if nutrition_result.target_daily_calories is not None:
        out["daily_calories"] = nutrition_result.target_daily_calories
    if nutrition_result.protein_pct is not None:
        out["macros"] = {
            "protein_pct": nutrition_result.protein_pct,
            "carbs_pct": nutrition_result.carbs_pct,
            "fat_pct": nutrition_result.fat_pct,
        }
    out["nutrition_engine"] = nutrition_result.to_plan_engine_dict()
    out["macro_grams"] = nutrition_result.to_plan_macro_grams_dict()
    out["macro_percentages"] = nutrition_result.to_plan_macro_pct_dict()
    out["alerts"] = nutrition_result.alerts_as_json()
    out["clinical_rules_applied"] = list(nutrition_result.clinical_rules_applied)
    out["applied_mode"] = nutrition_result.applied_mode.value
    out["applied_preferences"] = nutrition_result.applied_preferences
    out["manual_override_used"] = nutrition_result.manual_override_used
    out["override_warnings"] = list(nutrition_result.override_warnings)
    if nutrition_input is not None:
        out["contextual_factors"] = _contextual_to_dict(nutrition_input.contextual)
    return out
