"""Mapeo estado Telegram → kwargs del servicio de dietas."""

from app.services.telegram_diet_strategy import diet_strategy_kwargs_from_state


def test_kwargs_auto_minimal():
    assert diet_strategy_kwargs_from_state({}) == {
        "meals_per_day": 4,
        "strategy_mode": "auto",
    }
    assert diet_strategy_kwargs_from_state({"strategy_mode": "auto"}) == {
        "meals_per_day": 4,
        "strategy_mode": "auto"
    }


def test_kwargs_guided_style_and_macros():
    st = {
        "strategy_mode": "guided",
        "diet_style": "low_carb",
        "macro_protein": "high",
        "macro_carbs": "low",
    }
    k = diet_strategy_kwargs_from_state(st)
    assert k["meals_per_day"] == 4
    assert k["strategy_mode"] == "guided"
    assert k["diet_style"] == "low_carb"
    assert k["macro_mode"] == {"protein": "high", "carbs": "low"}


def test_kwargs_manual_targets():
    st = {
        "strategy_mode": "manual",
        "manual_kcal": 1800,
        "manual_protein_g": 120.0,
    }
    k = diet_strategy_kwargs_from_state(st)
    assert k["meals_per_day"] == 4
    assert k["strategy_mode"] == "manual"
    assert k["manual_targets"] == {
        "daily_calories": 1800.0,
        "protein_g": 120.0,
    }


def test_kwargs_respects_meals_per_day():
    st = {
        "meals_per_day": 5,
        "strategy_mode": "guided",
    }
    k = diet_strategy_kwargs_from_state(st)
    assert k["meals_per_day"] == 5
    assert k["strategy_mode"] == "guided"
