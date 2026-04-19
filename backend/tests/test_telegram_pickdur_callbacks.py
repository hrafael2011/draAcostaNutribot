"""Callbacks diet:pickdur y diet:pickrdur (mocks, sin BD real)."""

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


def test_pickdur_rejects_wrong_awaiting(monkeypatch: pytest.MonkeyPatch):
    msgs: list[str] = []
    mock_db = MagicMock()

    async def fake_doctor(db, uid: str):
        d = MagicMock()
        d.id = 1
        return d

    async def fake_load_state(db, doctor_id, key):
        return {"awaiting": "diet_note_offer", "patient_id": 5}

    async def cap_send(cid, text, **kwargs):
        msgs.append(text)

    async def cap_answer(cb_id, **kwargs):
        return None

    monkeypatch.setattr(telegram_handler, "_doctor_for_telegram_user", fake_doctor)
    monkeypatch.setattr(telegram_handler, "_load_state", fake_load_state)
    monkeypatch.setattr(telegram_handler, "send_telegram_message", cap_send)
    monkeypatch.setattr(
        telegram_handler, "answer_telegram_callback_query", cap_answer
    )

    async def run():
        ok = await telegram_handler._handle_callback_query(
            mock_db, _cb_update("diet:pickdur:5:21")
        )
        assert ok is True

    asyncio.run(run())
    assert any("Este paso ya no aplica" in m for m in msgs)


def test_pickdur_rejects_patient_id_mismatch(monkeypatch: pytest.MonkeyPatch):
    msgs: list[str] = []
    mock_db = MagicMock()

    async def fake_doctor(db, uid: str):
        d = MagicMock()
        d.id = 1
        return d

    async def fake_load_state(db, doctor_id, key):
        return {"awaiting": "diet_duration", "patient_id": 5, "instruction": None}

    async def cap_send(cid, text, **kwargs):
        msgs.append(text)

    async def cap_answer(cb_id, **kwargs):
        return None

    monkeypatch.setattr(telegram_handler, "_doctor_for_telegram_user", fake_doctor)
    monkeypatch.setattr(telegram_handler, "_load_state", fake_load_state)
    monkeypatch.setattr(telegram_handler, "send_telegram_message", cap_send)
    monkeypatch.setattr(
        telegram_handler, "answer_telegram_callback_query", cap_answer
    )

    async def run():
        await telegram_handler._handle_callback_query(
            mock_db, _cb_update("diet:pickdur:6:21")
        )

    asyncio.run(run())
    assert any("Este paso ya no aplica" in m for m in msgs)


def test_pickdur_calls_transition_when_state_ok(monkeypatch: pytest.MonkeyPatch):
    transition_calls: list[tuple] = []
    mock_db = MagicMock()
    patient = MagicMock()
    patient.id = 5
    patient.first_name = "Ana"
    patient.last_name = "Lopez"

    async def fake_doctor(db, uid: str):
        d = MagicMock()
        d.id = 1
        return d

    async def fake_load_state(db, doctor_id, key):
        return {
            "awaiting": "diet_duration",
            "patient_id": 5,
            "instruction": "baja sal",
        }

    async def fake_get_dp(db, doctor_id, pid):
        return patient if pid == 5 else None

    async def fake_transition(
        db, doctor, chat_id, channel_user_key, pat, instruction, ddays
    ):
        transition_calls.append((pat.id, instruction, ddays))

    async def cap_send(cid, text, **kwargs):
        pass

    async def cap_answer(cb_id, **kwargs):
        return None

    monkeypatch.setattr(telegram_handler, "_doctor_for_telegram_user", fake_doctor)
    monkeypatch.setattr(telegram_handler, "_load_state", fake_load_state)
    monkeypatch.setattr(telegram_handler, "get_doctor_patient", fake_get_dp)
    monkeypatch.setattr(
        telegram_handler,
        "_transition_new_diet_duration_to_strategy",
        fake_transition,
    )
    monkeypatch.setattr(telegram_handler, "send_telegram_message", cap_send)
    monkeypatch.setattr(
        telegram_handler, "answer_telegram_callback_query", cap_answer
    )

    async def run():
        await telegram_handler._handle_callback_query(
            mock_db, _cb_update("diet:pickdur:5:28")
        )

    asyncio.run(run())
    assert transition_calls == [(5, "baja sal", 28)]


def test_pickrdur_calls_transition_to_strategy_when_state_ok(
    monkeypatch: pytest.MonkeyPatch,
):
    transition_calls: list[tuple] = []
    mock_db = MagicMock()
    patient = MagicMock()
    patient.id = 3
    patient.first_name = "Luis"
    patient.last_name = "Pérez"

    async def fake_doctor(db, uid: str):
        d = MagicMock()
        d.id = 1
        return d

    async def fake_load_state(db, doctor_id, key):
        return {
            "awaiting": "diet_regenerate_duration",
            "pending_diet_id": 77,
            "patient_id": 3,
            "regen_instruction": "más verdura",
        }

    async def fake_get_dp(db, doctor_id, pid):
        return patient if pid == 3 else None

    async def fake_transition(
        db,
        doctor,
        chat_id,
        channel_user_key,
        pat,
        diet_id,
        regen_instruction,
        ddays,
    ):
        transition_calls.append((pat.id, diet_id, regen_instruction, ddays))

    async def cap_send(cid, text, **kwargs):
        pass

    async def cap_answer(cb_id, **kwargs):
        return None

    monkeypatch.setattr(telegram_handler, "_doctor_for_telegram_user", fake_doctor)
    monkeypatch.setattr(telegram_handler, "_load_state", fake_load_state)
    monkeypatch.setattr(telegram_handler, "get_doctor_patient", fake_get_dp)
    monkeypatch.setattr(
        telegram_handler,
        "_transition_regen_duration_to_strategy",
        fake_transition,
    )
    monkeypatch.setattr(telegram_handler, "send_telegram_message", cap_send)
    monkeypatch.setattr(
        telegram_handler, "answer_telegram_callback_query", cap_answer
    )

    async def run():
        await telegram_handler._handle_callback_query(
            mock_db, _cb_update("diet:pickrdur:77:364")
        )

    asyncio.run(run())
    assert transition_calls == [(3, 77, "más verdura", 364)]


def test_pickrdur_rejects_diet_id_mismatch(monkeypatch: pytest.MonkeyPatch):
    msgs: list[str] = []
    mock_db = MagicMock()

    async def fake_doctor(db, uid: str):
        d = MagicMock()
        d.id = 1
        return d

    async def fake_load_state(db, doctor_id, key):
        return {
            "awaiting": "diet_regenerate_duration",
            "pending_diet_id": 77,
            "patient_id": 3,
            "regen_instruction": "",
        }

    async def cap_send(cid, text, **kwargs):
        msgs.append(text)

    async def cap_answer(cb_id, **kwargs):
        return None

    monkeypatch.setattr(telegram_handler, "_doctor_for_telegram_user", fake_doctor)
    monkeypatch.setattr(telegram_handler, "_load_state", fake_load_state)
    monkeypatch.setattr(telegram_handler, "send_telegram_message", cap_send)
    monkeypatch.setattr(
        telegram_handler, "answer_telegram_callback_query", cap_answer
    )

    async def run():
        await telegram_handler._handle_callback_query(
            mock_db, _cb_update("diet:pickrdur:78:14")
        )

    asyncio.run(run())
    assert any("Este paso ya no aplica" in m for m in msgs)
