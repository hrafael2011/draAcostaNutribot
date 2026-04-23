"""Mapeo estado de conversación Telegram → kwargs de create_new_diet / regenerate_diet."""

from __future__ import annotations

from typing import Any, Optional

from app.services.plan_meals import meal_slots_for_count, meal_structure_summary_es, normalize_meals_per_day

# Códigos en callback_data (1 carácter) → valor API diet_style
STYLE_CODE_TO_API: dict[str, Optional[str]] = {
    "n": None,
    "b": "balanced",
    "l": "low_carb",
    "h": "high_carb",
    "p": "high_protein",
    "m": "mediterranean",
}

API_TO_STYLE_LABEL: dict[str, str] = {
    "balanced": "Equilibrada",
    "low_carb": "Baja en carbohidratos",
    "high_carb": "Alta en carbohidratos",
    "high_protein": "Alta en proteína",
    "mediterranean": "Mediterránea",
}

_MACRO_LEVELS = frozenset({"low", "normal", "high"})


def diet_strategy_kwargs_from_state(state: dict[str, Any]) -> dict[str, Any]:
    """Replica la lógica de frontend/src/utils/dietStrategyBody.ts."""
    sm = state.get("strategy_mode")
    if sm not in ("auto", "guided", "manual"):
        sm = "auto"
    meals_per_day = normalize_meals_per_day(state.get("meals_per_day"))
    out: dict[str, Any] = {
        "meals_per_day": meals_per_day,
        "strategy_mode": sm,
    }
    if sm == "auto":
        return out

    ds = state.get("diet_style")
    if isinstance(ds, str) and ds.strip():
        out["diet_style"] = ds.strip()

    if sm == "guided":
        macro: dict[str, str] = {}
        for src_key, api_key in (
            ("macro_protein", "protein"),
            ("macro_carbs", "carbs"),
            ("macro_fat", "fat"),
        ):
            v = state.get(src_key)
            if v in _MACRO_LEVELS:
                macro[api_key] = v
        if macro:
            out["macro_mode"] = macro

    if sm == "manual":
        mt: dict[str, float] = {}
        kcal = state.get("manual_kcal")
        if isinstance(kcal, (int, float)) and kcal > 0:
            mt["daily_calories"] = float(kcal)
        for src, dst in (
            ("manual_protein_g", "protein_g"),
            ("manual_carbs_g", "carbs_g"),
            ("manual_fat_g", "fat_g"),
        ):
            v = state.get(src)
            if isinstance(v, (int, float)) and v > 0:
                mt[dst] = float(v)
        if mt:
            out["manual_targets"] = mt

    return out


def strategy_summary_lines(state: dict[str, Any]) -> list[str]:
    """Texto legible para pantalla de confirmación (español)."""
    sm = state.get("strategy_mode")
    if sm not in ("auto", "guided", "manual"):
        sm = "auto"
    meals_per_day = normalize_meals_per_day(state.get("meals_per_day"))
    slots = meal_slots_for_count(meals_per_day)
    lines: list[str] = []
    lines.append(f"Comidas por día: {meals_per_day}.")
    lines.append(f"Estructura diaria: {meal_structure_summary_es(slots)}.")
    if sm == "auto":
        lines.append("Modo nutricional: Automático (cálculo estándar).")
        return lines
    if sm == "guided":
        lines.append("Modo nutricional: Guiado.")
        ds = state.get("diet_style")
        if isinstance(ds, str) and ds.strip():
            label = API_TO_STYLE_LABEL.get(ds.strip(), ds.strip())
            lines.append(f"Estilo: {label}.")
        else:
            lines.append("Estilo: sin estilo específico.")
        prefs: list[str] = []
        for label_es, key in (
            ("Proteína", "macro_protein"),
            ("Carbohidratos", "macro_carbs"),
            ("Grasas", "macro_fat"),
        ):
            v = state.get(key)
            if v in _MACRO_LEVELS:
                lv = {"low": "baja", "normal": "normal", "high": "alta"}[v]
                prefs.append(f"{label_es}: {lv}")
        if prefs:
            lines.append("Preferencias de macros: " + "; ".join(prefs) + ".")
        else:
            lines.append("Preferencias de macros: predeterminadas del sistema.")
        return lines
    # manual
    lines.append("Modo nutricional: Manual.")
    parts: list[str] = []
    kcal = state.get("manual_kcal")
    if isinstance(kcal, (int, float)) and kcal > 0:
        parts.append(f"{int(kcal)} kcal/día")
    for label, key in (
        ("P", "manual_protein_g"),
        ("C", "manual_carbs_g"),
        ("G", "manual_fat_g"),
    ):
        v = state.get(key)
        if isinstance(v, (int, float)) and v > 0:
            parts.append(f"{label} {v:g} g/día")
    if parts:
        lines.append("Objetivos manuales: " + ", ".join(parts) + ".")
    else:
        lines.append(
            "Objetivos manuales: orientación automática (sin cifras fijadas)."
        )
    return lines
