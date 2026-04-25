"""Vista previa de dieta: exige conversación en diet_preview + pending_diet_id."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services import telegram_handler


def _cb_update(data: str, *, user_id: int = 42, chat_id: int = 100) -> dict:
    return {
        "callback_query": {
            "id": "cb-test",
            "from": {"id": user_id, "username": "doc"},
            "data": data,
            "message": {"chat": {"id": chat_id, "type": "private"}, "message_id": 55},
        }
    }


def test_preview_approve_blocked_without_session(monkeypatch: pytest.MonkeyPatch):
    sent: list[str] = []
    approve_mock = AsyncMock()

    async def fake_doctor(db, uid: str):
        d = MagicMock()
        d.id = 1
        return d

    diet = MagicMock()
    diet.id = 9
    diet.doctor_id = 1
    diet.status = "pending_approval"
    diet.patient_id = 3
    diet.notes = ""

    async def fake_load_state(db, doctor_id, key):
        return {"awaiting": "diet_confirm", "patient_id": 3}

    async def cap_send(cid, text, **kwargs):
        sent.append(text)

    async def fake_stale(*args, **kwargs):
        await cap_send("100", "Este paso ya no aplica.")

    mock_db = MagicMock()

    async def mock_get(cls, did):
        return diet if did == 9 else None

    mock_db.get = mock_get

    monkeypatch.setattr(telegram_handler, "_doctor_for_telegram_user", fake_doctor)
    monkeypatch.setattr(telegram_handler, "_load_state", fake_load_state)
    monkeypatch.setattr(
        telegram_handler,
        "_send_stale_step_refresh",
        AsyncMock(side_effect=fake_stale),
    )
    monkeypatch.setattr(telegram_handler, "send_telegram_message", cap_send)
    monkeypatch.setattr(
        telegram_handler, "answer_telegram_callback_query", AsyncMock()
    )
    monkeypatch.setattr(
        telegram_handler, "edit_telegram_message_reply_markup", AsyncMock()
    )
    monkeypatch.setattr(telegram_handler, "approve_diet_preview", approve_mock)

    asyncio.run(
        telegram_handler._handle_callback_query(
            mock_db, _cb_update("diet:preview:approve:9")
        )
    )
    assert any("Este paso ya no aplica" in t for t in sent)
    approve_mock.assert_not_called()


def test_preview_approve_when_session_matches(monkeypatch: pytest.MonkeyPatch):
    approved: list[int] = []

    async def fake_doctor(db, uid: str):
        d = MagicMock()
        d.id = 1
        return d

    diet = MagicMock()
    diet.id = 9
    diet.doctor_id = 1
    diet.status = "pending_approval"
    diet.patient_id = 3
    diet.notes = ""

    async def fake_load_state(db, doctor_id, key):
        return {
            "awaiting": "diet_preview",
            "pending_diet_id": 9,
            "patient_id": 3,
            "preview_message_id": 55,
        }

    async def fake_load_state_for_update(db, doctor_id, key):
        return {
            "awaiting": "diet_preview",
            "pending_diet_id": 9,
            "patient_id": 3,
            "preview_message_id": 55,
        }

    async def fake_approve(db, doctor, diet_id):
        approved.append(diet_id)
        diet.status = "approved"
        return diet

    async def cap_send(cid, text, **kwargs):
        pass

    mock_db = MagicMock()

    async def mock_get(cls, did):
        return diet if did == 9 else None

    mock_db.get = mock_get

    monkeypatch.setattr(telegram_handler, "_doctor_for_telegram_user", fake_doctor)
    monkeypatch.setattr(telegram_handler, "_load_state", fake_load_state)
    monkeypatch.setattr(
        telegram_handler, "_load_state_for_update", fake_load_state_for_update
    )
    monkeypatch.setattr(telegram_handler, "send_telegram_message", cap_send)
    monkeypatch.setattr(
        telegram_handler, "answer_telegram_callback_query", AsyncMock()
    )
    monkeypatch.setattr(
        telegram_handler, "edit_telegram_message_reply_markup", AsyncMock()
    )
    monkeypatch.setattr(telegram_handler, "_clear_state", AsyncMock())
    monkeypatch.setattr(telegram_handler, "_save_state", AsyncMock())
    monkeypatch.setattr(telegram_handler, "_send_diet_pdf", AsyncMock())
    monkeypatch.setattr(telegram_handler, "approve_diet_preview", fake_approve)
    monkeypatch.setattr(
        telegram_handler,
        "get_doctor_patient",
        AsyncMock(return_value=MagicMock()),
    )

    asyncio.run(
        telegram_handler._handle_callback_query(
            mock_db, _cb_update("diet:preview:approve:9")
        )
    )
    assert approved == [9]
