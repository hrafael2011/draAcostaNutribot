from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services import telegram_handler


def _cb_update(
    data: str,
    *,
    message_id: int,
    user_id: int = 42,
    chat_id: int = 100,
) -> dict:
    return {
        "callback_query": {
            "id": "cb-test",
            "from": {"id": user_id, "username": "doc"},
            "data": data,
            "message": {
                "chat": {"id": chat_id, "type": "private"},
                "message_id": message_id,
            },
        }
    }


def test_diet_confirm_rejects_old_message_id(monkeypatch: pytest.MonkeyPatch):
    sent: list[str] = []
    exec_mock = AsyncMock()

    async def fake_doctor(db, uid: str):
        d = MagicMock()
        d.id = 1
        return d

    patient = MagicMock()
    patient.id = 5

    async def fake_get_patient(db, doctor_id, pid):
        return patient if pid == 5 else None

    async def fake_load_state_for_update(db, doctor_id, key):
        return {
            "awaiting": "diet_confirm",
            "patient_id": 5,
            "confirm_message_id": 777,
        }

    async def cap_send(cid, text, **kwargs):
        sent.append(text)

    async def fake_stale(*args, **kwargs):
        await cap_send("100", "Este paso ya no aplica.")

    monkeypatch.setattr(telegram_handler, "_doctor_for_telegram_user", fake_doctor)
    monkeypatch.setattr(telegram_handler, "get_doctor_patient", fake_get_patient)
    monkeypatch.setattr(
        telegram_handler, "_load_state_for_update", fake_load_state_for_update
    )
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
    monkeypatch.setattr(
        telegram_handler, "_execute_diet_confirm_from_snapshot", exec_mock
    )
    monkeypatch.setattr(telegram_handler, "_send_diet_confirm_prompt", AsyncMock())

    asyncio.run(
        telegram_handler._handle_callback_query(
            MagicMock(), _cb_update("diet:confirm:5", message_id=701)
        )
    )

    exec_mock.assert_not_called()
    assert any("Este paso ya no aplica" in text for text in sent)


def test_preview_quickmenu_rejects_replaced_preview_message(
    monkeypatch: pytest.MonkeyPatch,
):
    sent: list[str] = []
    quick_menu_mock = AsyncMock()

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
            "preview_message_id": 888,
        }

    async def cap_send(cid, text, **kwargs):
        sent.append(text)

    async def fake_stale(*args, **kwargs):
        await cap_send("100", "Este mensaje ya fue reemplazado por otro más reciente.")

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
    monkeypatch.setattr(
        telegram_handler, "_send_diet_quick_adjust_menu", quick_menu_mock
    )

    asyncio.run(
        telegram_handler._handle_callback_query(
            mock_db, _cb_update("diet:preview:quickmenu:9", message_id=777)
        )
    )

    quick_menu_mock.assert_not_called()
    assert any("reemplazado por otro más reciente" in text for text in sent)
