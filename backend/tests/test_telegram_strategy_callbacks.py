"""Callbacks diet:smd (modo nutricional)."""

from __future__ import annotations

import asyncio
from unittest.mock import MagicMock

import pytest

from app.services import telegram_handler


def _cb_update(data: str, *, user_id: int = 42, chat_id: int = 100) -> dict:
    return {
        "callback_query": {
            "id": "cb-test",
            "from": {"id": user_id, "username": "doc"},
            "data": data,
            "message": {"chat": {"id": chat_id, "type": "private"}},
        }
    }


def test_smd_guided_triggers_style_step(monkeypatch: pytest.MonkeyPatch):
    sent: list[tuple[str, dict]] = []
    saved: list[dict] = []
    mock_db = MagicMock()

    async def fake_doctor(db, uid: str):
        d = MagicMock()
        d.id = 1
        return d

    async def fake_load_state(db, doctor_id, key):
        return {
            "awaiting": "diet_strategy_mode",
            "strategy_flow": "new",
            "patient_id": 5,
            "instruction": None,
            "duration_days": 7,
        }

    patient = MagicMock()
    patient.id = 5
    patient.first_name = "Ana"
    patient.last_name = "Lopez"

    async def fake_get_dp(db, doctor_id, pid):
        return patient if pid == 5 else None

    async def cap_save(db, doctor_id, key, payload):
        saved.append(dict(payload))

    async def cap_send(cid, text, **kwargs):
        sent.append((text, kwargs.get("reply_markup") or {}))

    async def cap_answer(cb_id, **kwargs):
        return None

    monkeypatch.setattr(telegram_handler, "_doctor_for_telegram_user", fake_doctor)
    monkeypatch.setattr(telegram_handler, "_load_state", fake_load_state)
    monkeypatch.setattr(telegram_handler, "get_doctor_patient", fake_get_dp)
    monkeypatch.setattr(telegram_handler, "_save_state", cap_save)
    monkeypatch.setattr(telegram_handler, "send_telegram_message", cap_send)
    monkeypatch.setattr(
        telegram_handler, "answer_telegram_callback_query", cap_answer
    )

    async def run():
        await telegram_handler._handle_callback_query(
            mock_db, _cb_update("diet:smd:g:5")
        )

    asyncio.run(run())
    assert saved and saved[-1].get("awaiting") == "diet_strategy_style"
    assert saved[-1].get("strategy_mode") == "guided"
    assert any("Estilo" in t for t, _ in sent)


def test_smd_auto_goes_to_confirm(monkeypatch: pytest.MonkeyPatch):
    persist_calls: list[dict] = []
    mock_db = MagicMock()

    async def fake_doctor(db, uid: str):
        d = MagicMock()
        d.id = 1
        return d

    async def fake_load_state(db, doctor_id, key):
        return {
            "awaiting": "diet_strategy_mode",
            "strategy_flow": "new",
            "patient_id": 5,
            "instruction": "sin gluten",
            "duration_days": 14,
        }

    patient = MagicMock()
    patient.id = 5
    patient.first_name = "Ana"
    patient.last_name = "Lopez"

    async def fake_get_dp(db, doctor_id, pid):
        return patient if pid == 5 else None

    async def fake_persist(db, doctor, cid, key, wizard_state):
        persist_calls.append(dict(wizard_state))

    async def cap_send(cid, text, **kwargs):
        pass

    async def cap_answer(cb_id, **kwargs):
        return None

    monkeypatch.setattr(telegram_handler, "_doctor_for_telegram_user", fake_doctor)
    monkeypatch.setattr(telegram_handler, "_load_state", fake_load_state)
    monkeypatch.setattr(telegram_handler, "get_doctor_patient", fake_get_dp)
    monkeypatch.setattr(
        telegram_handler,
        "_persist_diet_confirm_and_show",
        fake_persist,
    )
    monkeypatch.setattr(telegram_handler, "send_telegram_message", cap_send)
    monkeypatch.setattr(
        telegram_handler, "answer_telegram_callback_query", cap_answer
    )

    async def run():
        await telegram_handler._handle_callback_query(
            mock_db, _cb_update("diet:smd:a:5")
        )

    asyncio.run(run())
    assert persist_calls
    assert persist_calls[0].get("strategy_mode") == "auto"
    assert persist_calls[0].get("duration_days") == 14


def test_smd_manual_triggers_manual_kcal_step(monkeypatch: pytest.MonkeyPatch):
    sent: list[tuple[str, dict]] = []
    saved: list[dict] = []
    mock_db = MagicMock()

    async def fake_doctor(db, uid: str):
        d = MagicMock()
        d.id = 1
        return d

    async def fake_load_state(db, doctor_id, key):
        return {
            "awaiting": "diet_strategy_mode",
            "strategy_flow": "new",
            "patient_id": 5,
            "instruction": "sin lactosa",
            "duration_days": 21,
            "meals_per_day": 3,
        }

    patient = MagicMock()
    patient.id = 5
    patient.first_name = "Ana"
    patient.last_name = "Lopez"

    async def fake_get_dp(db, doctor_id, pid):
        return patient if pid == 5 else None

    async def cap_save(db, doctor_id, key, payload):
        saved.append(dict(payload))

    async def cap_send(cid, text, **kwargs):
        sent.append((text, kwargs.get("reply_markup") or {}))

    async def cap_answer(cb_id, **kwargs):
        return None

    monkeypatch.setattr(telegram_handler, "_doctor_for_telegram_user", fake_doctor)
    monkeypatch.setattr(telegram_handler, "_load_state", fake_load_state)
    monkeypatch.setattr(telegram_handler, "get_doctor_patient", fake_get_dp)
    monkeypatch.setattr(telegram_handler, "_save_state", cap_save)
    monkeypatch.setattr(telegram_handler, "send_telegram_message", cap_send)
    monkeypatch.setattr(
        telegram_handler, "answer_telegram_callback_query", cap_answer
    )

    async def run():
        await telegram_handler._handle_callback_query(
            mock_db, _cb_update("diet:smd:m:5")
        )

    asyncio.run(run())
    assert saved and saved[-1].get("awaiting") == "diet_manual_kcal"
    assert saved[-1].get("strategy_mode") == "manual"
    assert saved[-1].get("meals_per_day") == 3
    assert any("calor" in t.lower() for t, _ in sent)


def test_meals_callback_moves_to_strategy_mode(monkeypatch: pytest.MonkeyPatch):
    sent: list[tuple[str, dict]] = []
    saved: list[dict] = []
    mock_db = MagicMock()

    async def fake_doctor(db, uid: str):
        d = MagicMock()
        d.id = 1
        return d

    async def fake_load_state(db, doctor_id, key):
        return {
            "awaiting": "diet_meals_per_day",
            "strategy_flow": "new",
            "patient_id": 5,
            "instruction": None,
            "duration_days": 14,
        }

    async def cap_save(db, doctor_id, key, payload):
        saved.append(dict(payload))

    async def cap_send(cid, text, **kwargs):
        sent.append((text, kwargs.get("reply_markup") or {}))

    async def cap_answer(cb_id, **kwargs):
        return None

    monkeypatch.setattr(telegram_handler, "_doctor_for_telegram_user", fake_doctor)
    monkeypatch.setattr(telegram_handler, "_load_state", fake_load_state)
    monkeypatch.setattr(telegram_handler, "_save_state", cap_save)
    monkeypatch.setattr(telegram_handler, "send_telegram_message", cap_send)
    monkeypatch.setattr(
        telegram_handler, "answer_telegram_callback_query", cap_answer
    )

    async def run():
        await telegram_handler._handle_callback_query(
            mock_db, _cb_update("diet:meals:5:5")
        )

    asyncio.run(run())
    assert saved and saved[-1].get("meals_per_day") == 5
    assert saved[-1].get("awaiting") == "diet_strategy_mode"
    assert any("Automático" in t or "objetivos nutricionales" in t for t, _ in sent)
