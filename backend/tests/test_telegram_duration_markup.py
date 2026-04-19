"""Markup de atajos de duración en Telegram (sin webhook ni BD)."""

from app.logic.diet_duration import MAX_PLAN_DURATION_DAYS, QUICK_PLAN_DURATION_DAYS
from app.services.telegram_diet_ui import (
    diet_duration_choice_markup,
    diet_regen_duration_choice_markup,
)


def test_quick_duration_values_are_valid_multiples():
    for d in QUICK_PLAN_DURATION_DAYS:
        assert d % 7 == 0
        assert 7 <= d <= MAX_PLAN_DURATION_DAYS


def test_duration_choice_markup_callbacks():
    patient_id = 501
    m = diet_duration_choice_markup(patient_id)
    flat = [btn for row in m["inline_keyboard"] for btn in row]
    pick = [b for b in flat if b["callback_data"].startswith("diet:pickdur:")]
    assert len(pick) == len(QUICK_PLAN_DURATION_DAYS)
    assert {"text": "7 d", "callback_data": f"diet:pickdur:{patient_id}:7"} in pick
    assert {"text": "112 d", "callback_data": f"diet:pickdur:{patient_id}:112"} in pick
    assert {"text": "364 d", "callback_data": f"diet:pickdur:{patient_id}:364"} in pick
    cancel = [b for b in flat if b["callback_data"] == "flow:cancel"]
    assert len(cancel) == 1


def test_regen_duration_choice_markup_callbacks():
    diet_id = 909
    m = diet_regen_duration_choice_markup(diet_id)
    flat = [btn for row in m["inline_keyboard"] for btn in row]
    pick = [b for b in flat if b["callback_data"].startswith("diet:pickrdur:")]
    assert len(pick) == len(QUICK_PLAN_DURATION_DAYS)
    assert {
        "text": "84 d",
        "callback_data": f"diet:pickrdur:{diet_id}:84",
    } in pick
    assert {
        "text": "364 d",
        "callback_data": f"diet:pickrdur:{diet_id}:364",
    } in pick
