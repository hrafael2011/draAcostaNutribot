"""Evitar duplicar arranque al pulsar otra vez «Generar dieta» (patient:diet)."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services import telegram_handler


def _cb(data: str) -> dict:
    return {
        "callback_query": {
            "id": "cb1",
            "from": {"id": 99},
            "data": data,
            "message": {"chat": {"id": 1, "type": "private"}, "message_id": 7},
        }
    }


def test_patient_diet_second_click_refreshes_not_restarts(monkeypatch: pytest.MonkeyPatch):
    sent: list[str] = []
    starts: list[int] = []

    async def fake_doctor(db, uid: str):
        d = MagicMock()
        d.id = 1
        return d

    patient = MagicMock()
    patient.id = 5

    async def fake_guard(*a, **k):
        return True

    async def fake_get_patient(db, doctor_id, pid):
        return patient if pid == 5 else None

    async def fake_load_state(db, doctor_id, key):
        return {"awaiting": "diet_note_offer", "patient_id": 5}

    async def fake_start(db, doctor, chat_id, key, pat):
        starts.append(pat.id)

    async def fake_refresh(db, doctor, chat_id, key, *, prefix: str = ""):
        sent.append(prefix)

    async def cap_send(cid, text, **kwargs):
        sent.append(text)

    monkeypatch.setattr(telegram_handler, "_doctor_for_telegram_user", fake_doctor)
    monkeypatch.setattr(telegram_handler, "_guard_active_patient_switch", fake_guard)
    monkeypatch.setattr(telegram_handler, "get_doctor_patient", fake_get_patient)
    monkeypatch.setattr(telegram_handler, "_load_state", fake_load_state)
    monkeypatch.setattr(telegram_handler, "_start_guided_diet_flow", fake_start)
    monkeypatch.setattr(telegram_handler, "_send_stale_step_refresh", fake_refresh)
    monkeypatch.setattr(telegram_handler, "send_telegram_message", cap_send)
    monkeypatch.setattr(
        telegram_handler, "answer_telegram_callback_query", AsyncMock()
    )
    monkeypatch.setattr(
        telegram_handler, "edit_telegram_message_reply_markup", AsyncMock()
    )

    asyncio.run(
        telegram_handler._handle_callback_query(MagicMock(), _cb("patient:diet:5"))
    )
    assert starts == []
    assert any("Ya tienes un flujo de dieta abierto" in s for s in sent)


def test_patient_diet_first_click_starts_flow(monkeypatch: pytest.MonkeyPatch):
    starts: list[int] = []

    async def fake_doctor(db, uid: str):
        d = MagicMock()
        d.id = 1
        return d

    patient = MagicMock()
    patient.id = 5

    async def fake_guard(*a, **k):
        return True

    async def fake_get_patient(db, doctor_id, pid):
        return patient if pid == 5 else None

    async def fake_load_state(db, doctor_id, key):
        return {"awaiting": "search_query"}

    async def fake_start(db, doctor, chat_id, key, pat):
        starts.append(pat.id)

    monkeypatch.setattr(telegram_handler, "_doctor_for_telegram_user", fake_doctor)
    monkeypatch.setattr(telegram_handler, "_guard_active_patient_switch", fake_guard)
    monkeypatch.setattr(telegram_handler, "get_doctor_patient", fake_get_patient)
    monkeypatch.setattr(telegram_handler, "_load_state", fake_load_state)
    monkeypatch.setattr(telegram_handler, "_start_guided_diet_flow", fake_start)
    monkeypatch.setattr(telegram_handler, "send_telegram_message", AsyncMock())
    monkeypatch.setattr(
        telegram_handler, "answer_telegram_callback_query", AsyncMock()
    )
    monkeypatch.setattr(
        telegram_handler, "edit_telegram_message_reply_markup", AsyncMock()
    )

    asyncio.run(
        telegram_handler._handle_callback_query(MagicMock(), _cb("patient:diet:5"))
    )
    assert starts == [5]
