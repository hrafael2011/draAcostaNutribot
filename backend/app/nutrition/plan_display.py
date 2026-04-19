"""Extracción legible de bloques del motor desde structured_plan_json (planes nuevos y legacy)."""

from __future__ import annotations

from typing import Any


def _plan_dict(plan: Any) -> dict[str, Any]:
    return plan if isinstance(plan, dict) else {}


def nutrition_engine_text_lines(plan: Any) -> list[str]:
    """Líneas en español para UI (Telegram, texto plano)."""
    p = _plan_dict(plan)
    ne = p.get("nutrition_engine")
    if not isinstance(ne, dict) or not ne:
        return []
    lines: list[str] = []
    ver = ne.get("engine_schema_version")
    if ver:
        lines.append(f"Motor nutricional (esquema {ver})")
    else:
        lines.append("Motor nutricional (calculado)")
    if ne.get("bmr_kcal") is not None:
        lines.append(f"· TMB estimada: {ne['bmr_kcal']} kcal/día")
    if ne.get("tdee_kcal") is not None:
        lines.append(f"· GET (TDEE) estimado: {ne['tdee_kcal']} kcal/día")
    if ne.get("activity_factor") is not None:
        lines.append(f"· Factor de actividad: {ne['activity_factor']}")
    if ne.get("bmi") is not None:
        lines.append(f"· IMC calculado: {ne['bmi']}")
    if ne.get("goal_calories") is not None:
        lines.append(f"· Objetivo calórico aplicado: {ne['goal_calories']} kcal/día")
    mode = ne.get("applied_mode")
    if mode and str(mode).strip() and str(mode) != "auto":
        lines.append(f"· Modo de objetivos: {mode}")
    if ne.get("manual_override_used") is True:
        lines.append("· Ajuste manual del profesional aplicado a calorías/macros")
    ow = ne.get("override_warnings")
    if isinstance(ow, list) and ow:
        for w in ow[:2]:
            s = str(w).strip()
            if not s:
                continue
            if len(s) > 200:
                s = s[:197] + "…"
            lines.append(f"· Aviso: {s}")
    return lines


def macro_grams_text_line(plan: Any) -> str | None:
    p = _plan_dict(plan)
    mg = p.get("macro_grams")
    if not isinstance(mg, dict):
        return None
    pg, cg, fg = mg.get("protein_g"), mg.get("carbs_g"), mg.get("fat_g")
    if pg is None and cg is None and fg is None:
        return None
    parts = []
    if pg is not None:
        parts.append(f"proteína ~{pg} g")
    if cg is not None:
        parts.append(f"hidratos ~{cg} g")
    if fg is not None:
        parts.append(f"grasas ~{fg} g")
    if not parts:
        return None
    return "Gramos orientativos/día: " + " · ".join(parts)


def clinical_rules_text_line(plan: Any) -> str | None:
    p = _plan_dict(plan)
    rules = p.get("clinical_rules_applied")
    if not isinstance(rules, list) or not rules:
        return None
    clean = [str(x).strip() for x in rules if str(x).strip()]
    if not clean:
        return None
    return "Reglas clínicas aplicadas (sistema): " + ", ".join(clean[:12])


def plan_duration_text_lines(plan: Any) -> list[str]:
    """Líneas sobre duración total y repetición del ciclo semanal."""
    p = _plan_dict(plan)
    d = p.get("plan_duration_days")
    if not isinstance(d, int) or d <= 0:
        return []
    weeks = p.get("plan_duration_weeks")
    if not isinstance(weeks, int):
        weeks = d // 7
    lines = [
        f"Duración total indicada: {d} días ({weeks} semana(s)); ciclo base en el plan: 7 días."
    ]
    instr = p.get("plan_repeat_instruction_es")
    if isinstance(instr, str) and instr.strip():
        s = instr.strip()
        cut = 320
        lines.append(s[:cut] + ("…" if len(s) > cut else ""))
    return lines


def alerts_text_lines(
    plan: Any,
    *,
    max_items: int = 8,
    max_len: int = 220,
) -> list[str]:
    p = _plan_dict(plan)
    raw = p.get("alerts")
    if not isinstance(raw, list) or not raw:
        return []
    lines: list[str] = []
    for item in raw[:max_items]:
        if not isinstance(item, dict):
            continue
        sev = str(item.get("severity") or "info").upper()
        msg = str(item.get("message_es") or item.get("message") or "").strip()
        if not msg:
            continue
        if len(msg) > max_len:
            msg = msg[: max_len - 1] + "…"
        lines.append(f"[{sev}] {msg}")
    return lines
