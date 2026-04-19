from __future__ import annotations

from typing import Any

MealCount = int

MEAL_SLOT_LABELS_ES: dict[str, str] = {
    "breakfast": "Desayuno",
    "mid_morning_snack": "Media mañana",
    "lunch": "Almuerzo",
    "snack": "Merienda",
    "dinner": "Cena",
}

MEAL_SLOT_PATTERNS: dict[int, tuple[str, ...]] = {
    2: ("breakfast", "dinner"),
    3: ("breakfast", "lunch", "dinner"),
    4: ("breakfast", "lunch", "snack", "dinner"),
    5: ("breakfast", "mid_morning_snack", "lunch", "snack", "dinner"),
}

ALL_MEAL_SLOTS: tuple[str, ...] = tuple(
    dict.fromkeys(slot for slots in MEAL_SLOT_PATTERNS.values() for slot in slots)
)


def normalize_meals_per_day(raw: Any, *, default: int = 4) -> int:
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return default
    return value if value in MEAL_SLOT_PATTERNS else default


def meal_slots_for_count(meals_per_day: int) -> list[str]:
    return list(MEAL_SLOT_PATTERNS[normalize_meals_per_day(meals_per_day)])


def meal_slot_label_es(slot_id: str) -> str:
    return MEAL_SLOT_LABELS_ES.get(slot_id, slot_id.replace("_", " ").title())


def meal_structure_summary_es(slots: list[str] | tuple[str, ...]) -> str:
    return ", ".join(meal_slot_label_es(slot).lower() for slot in slots)


def resolve_plan_meal_slots(plan: dict[str, Any]) -> list[str]:
    raw_slots = plan.get("meal_slots")
    if isinstance(raw_slots, list):
        slots = [
            str(slot).strip()
            for slot in raw_slots
            if isinstance(slot, str) and str(slot).strip() in ALL_MEAL_SLOTS
        ]
        if slots:
            deduped = list(dict.fromkeys(slots))
            if len(deduped) in MEAL_SLOT_PATTERNS:
                return deduped
    if any(isinstance(plan.get(k), str) for k in ALL_MEAL_SLOTS):
        return meal_slots_for_count(4)
    days = plan.get("days")
    if isinstance(days, list):
        for day in days:
            if not isinstance(day, dict):
                continue
            if isinstance(day.get("meals"), dict):
                slots = [
                    slot
                    for slot in ALL_MEAL_SLOTS
                    if isinstance(day["meals"].get(slot), str)
                ]
                if slots:
                    deduped = list(dict.fromkeys(slots))
                    if len(deduped) in MEAL_SLOT_PATTERNS:
                        return deduped
            slots = [slot for slot in ALL_MEAL_SLOTS if isinstance(day.get(slot), str)]
            if slots:
                deduped = list(dict.fromkeys(slots))
                if len(deduped) in MEAL_SLOT_PATTERNS:
                    return deduped
    return meal_slots_for_count(normalize_meals_per_day(plan.get("meals_per_day")))


def normalize_plan_meal_metadata(
    plan: dict[str, Any],
    *,
    requested_meals_per_day: int | None = None,
) -> dict[str, Any]:
    out = dict(plan)
    meals_per_day = normalize_meals_per_day(
        requested_meals_per_day
        if requested_meals_per_day is not None
        else out.get("meals_per_day")
    )
    slots = meal_slots_for_count(meals_per_day)
    out["meals_per_day"] = meals_per_day
    out["meal_slots"] = slots

    raw_days = out.get("days")
    if not isinstance(raw_days, list):
        return out

    normalized_days: list[dict[str, Any]] = []
    for idx, raw_day in enumerate(raw_days, start=1):
        if not isinstance(raw_day, dict):
            continue
        raw_meals = raw_day.get("meals")
        meals: dict[str, str] = {}
        for slot in slots:
            candidate: Any = None
            if isinstance(raw_meals, dict):
                candidate = raw_meals.get(slot)
            if candidate in (None, ""):
                candidate = raw_day.get(slot)
            if candidate is None:
                continue
            text = str(candidate).strip()
            if text:
                meals[slot] = text
        day_num = raw_day.get("day")
        if not isinstance(day_num, int):
            day_num = idx
        day_out: dict[str, Any] = {"day": day_num, "meals": meals}
        for slot in slots:
            day_out[slot] = meals.get(slot, "")
        normalized_days.append(day_out)
    out["days"] = normalized_days
    return out


def extract_day_meals(day: dict[str, Any], slots: list[str] | tuple[str, ...]) -> list[tuple[str, str, str]]:
    raw_meals = day.get("meals")
    out: list[tuple[str, str, str]] = []
    for slot in slots:
        candidate: Any = None
        if isinstance(raw_meals, dict):
            candidate = raw_meals.get(slot)
        if candidate in (None, ""):
            candidate = day.get(slot)
        text = str(candidate or "").strip()
        out.append((slot, meal_slot_label_es(slot), text))
    return out
