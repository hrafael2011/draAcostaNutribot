from __future__ import annotations

import asyncio
from unittest.mock import MagicMock

from app.services import telegram_handler


def _doctor() -> MagicMock:
    d = MagicMock()
    d.id = 1
    return d


def _patient() -> MagicMock:
    p = MagicMock()
    p.id = 5
    p.first_name = "Ana"
    p.last_name = "Lopez"
    return p


def test_stateful_meals_per_day_accepts_numeric_text(monkeypatch):
    state: dict = {
        "awaiting": "diet_meals_per_day",
        "patient_id": 5,
        "duration_days": 14,
        "strategy_flow": "new",
        "instruction": None,
    }
    sent: list[tuple[str, dict]] = []
    doctor = _doctor()
    patient = _patient()

    async def fake_load_state(db, doctor_id, key):
        return dict(state)

    async def fake_save_state(db, doctor_id, key, payload):
        state.update(payload)

    async def fake_get_patient(db, doctor_id, patient_id):
        return patient if patient_id == 5 else None

    async def fake_send_message(chat_id, text, **kwargs):
        sent.append((text, kwargs.get("reply_markup") or {}))

    async def run():
        handled = await telegram_handler._handle_stateful_text(
            MagicMock(),
            doctor,
            "chat-1",
            "telegram:42",
            "5",
        )
        assert handled is True

    monkeypatch.setattr(telegram_handler, "_load_state", fake_load_state)
    monkeypatch.setattr(telegram_handler, "_save_state", fake_save_state)
    monkeypatch.setattr(telegram_handler, "get_doctor_patient", fake_get_patient)
    monkeypatch.setattr(telegram_handler, "send_telegram_message", fake_send_message)

    asyncio.run(run())
    assert state["meals_per_day"] == 5
    assert state["awaiting"] == "diet_strategy_mode"
    assert any("objetivos nutricionales" in text.lower() for text, _ in sent)


def test_stateful_meals_per_day_rejects_invalid_text(monkeypatch):
    state: dict = {
        "awaiting": "diet_meals_per_day",
        "patient_id": 5,
        "duration_days": 14,
        "strategy_flow": "new",
    }
    sent: list[str] = []
    doctor = _doctor()
    patient = _patient()

    async def fake_load_state(db, doctor_id, key):
        return dict(state)

    async def fake_get_patient(db, doctor_id, patient_id):
        return patient if patient_id == 5 else None

    async def fake_send_message(chat_id, text, **kwargs):
        sent.append(text)

    async def run():
        handled = await telegram_handler._handle_stateful_text(
            MagicMock(),
            doctor,
            "chat-1",
            "telegram:42",
            "6 comidas",
        )
        assert handled is True

    monkeypatch.setattr(telegram_handler, "_load_state", fake_load_state)
    monkeypatch.setattr(telegram_handler, "get_doctor_patient", fake_get_patient)
    monkeypatch.setattr(telegram_handler, "send_telegram_message", fake_send_message)

    asyncio.run(run())
    assert state.get("meals_per_day") is None
    assert any("Elige 2, 3, 4 o 5 comidas por día." in text for text in sent)


def test_manual_stateful_flow_reaches_confirm_with_values(monkeypatch):
    state: dict = {
        "awaiting": "diet_manual_kcal",
        "patient_id": 5,
        "duration_days": 14,
        "strategy_flow": "new",
        "strategy_mode": "manual",
        "meals_per_day": 4,
        "instruction": "sin gluten",
    }
    sent: list[str] = []
    persisted: list[dict] = []
    doctor = _doctor()
    patient = _patient()

    async def fake_load_state(db, doctor_id, key):
        return dict(state)

    async def fake_save_state(db, doctor_id, key, payload):
        state.update(payload)

    async def fake_get_patient(db, doctor_id, patient_id):
        return patient if patient_id == 5 else None

    async def fake_send_message(chat_id, text, **kwargs):
        sent.append(text)

    async def fake_persist(db, doctor_obj, chat_id, channel_user_key, wizard_state):
        persisted.append(dict(wizard_state))

    monkeypatch.setattr(telegram_handler, "_load_state", fake_load_state)
    monkeypatch.setattr(telegram_handler, "_save_state", fake_save_state)
    monkeypatch.setattr(telegram_handler, "get_doctor_patient", fake_get_patient)
    monkeypatch.setattr(telegram_handler, "send_telegram_message", fake_send_message)
    monkeypatch.setattr(
        telegram_handler,
        "_persist_diet_confirm_and_show",
        fake_persist,
    )

    async def run():
        for text in ("1800", "120", "150", "60"):
            handled = await telegram_handler._handle_stateful_text(
                MagicMock(),
                doctor,
                "chat-1",
                "telegram:42",
                text,
            )
            assert handled is True

    asyncio.run(run())
    assert persisted
    snap = persisted[-1]
    assert snap["meals_per_day"] == 4
    assert snap["strategy_mode"] == "manual"
    assert snap["manual_kcal"] == 1800
    assert snap["manual_protein_g"] == 120.0
    assert snap["manual_carbs_g"] == 150.0
    assert snap["manual_fat_g"] == 60.0
    assert any("Proteína en g/día" in text for text in sent)
