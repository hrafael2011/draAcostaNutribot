from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services import telegram_handler
from app.services import telegram_diet_ui
from app.models import AuditLog


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


def test_menu_patients_rejects_old_navigation_message(
    monkeypatch: pytest.MonkeyPatch,
):
    async def fake_doctor(db, uid: str):
        d = MagicMock()
        d.id = 1
        return d

    stale_refresh = AsyncMock()
    send_patients = AsyncMock()
    edit_markup = AsyncMock()

    async def fake_load_state_for_update(db, doctor_id, key):
        return {
            "navigation_screen": "home",
            "navigation_message_id": 777,
        }

    monkeypatch.setattr(telegram_handler, "_doctor_for_telegram_user", fake_doctor)
    monkeypatch.setattr(
        telegram_handler, "_load_state_for_update", fake_load_state_for_update
    )
    monkeypatch.setattr(
        telegram_handler, "_send_stale_navigation_refresh", stale_refresh
    )
    monkeypatch.setattr(telegram_handler, "_send_patients_page", send_patients)
    monkeypatch.setattr(
        telegram_handler, "answer_telegram_callback_query", AsyncMock()
    )
    monkeypatch.setattr(
        telegram_handler, "edit_telegram_message_reply_markup", edit_markup
    )

    asyncio.run(
        telegram_handler._handle_callback_query(
            MagicMock(), _cb_update("menu:patients:1", message_id=701)
        )
    )

    stale_refresh.assert_awaited_once()
    send_patients.assert_not_called()
    edit_markup.assert_awaited_once()


def test_menu_patients_accepts_current_navigation_message(
    monkeypatch: pytest.MonkeyPatch,
):
    async def fake_doctor(db, uid: str):
        d = MagicMock()
        d.id = 1
        return d

    send_patients = AsyncMock()
    edit_markup = AsyncMock()

    async def fake_load_state_for_update(db, doctor_id, key):
        return {
            "navigation_screen": "home",
            "navigation_message_id": 701,
        }

    monkeypatch.setattr(telegram_handler, "_doctor_for_telegram_user", fake_doctor)
    monkeypatch.setattr(
        telegram_handler, "_load_state_for_update", fake_load_state_for_update
    )
    monkeypatch.setattr(telegram_handler, "_send_patients_page", send_patients)
    monkeypatch.setattr(
        telegram_handler, "answer_telegram_callback_query", AsyncMock()
    )
    monkeypatch.setattr(
        telegram_handler, "edit_telegram_message_reply_markup", edit_markup
    )

    asyncio.run(
        telegram_handler._handle_callback_query(
            MagicMock(), _cb_update("menu:patients:1", message_id=701)
        )
    )

    send_patients.assert_awaited_once()
    args, kwargs = send_patients.await_args
    assert args[3] == "telegram:42"
    assert kwargs["page"] == 1
    edit_markup.assert_awaited_once()


def test_nav_back_returns_to_previous_patients_screen(
    monkeypatch: pytest.MonkeyPatch,
):
    async def fake_doctor(db, uid: str):
        d = MagicMock()
        d.id = 1
        return d

    send_patients = AsyncMock()

    async def fake_load_state_for_update(db, doctor_id, key):
        return {
            "navigation_screen": "patient_card",
            "navigation_message_id": 701,
        }

    async def fake_load_state(db, doctor_id, key):
        return {
            "navigation_screen": "patient_card",
            "navigation_message_id": 701,
            "navigation_back_screen": "patients",
            "navigation_back_page": 3,
            "navigation_back_query": "maria",
        }

    monkeypatch.setattr(telegram_handler, "_doctor_for_telegram_user", fake_doctor)
    monkeypatch.setattr(
        telegram_handler, "_load_state_for_update", fake_load_state_for_update
    )
    monkeypatch.setattr(telegram_handler, "_load_state", fake_load_state)
    monkeypatch.setattr(telegram_handler, "_send_patients_page", send_patients)
    monkeypatch.setattr(
        telegram_handler, "answer_telegram_callback_query", AsyncMock()
    )
    monkeypatch.setattr(
        telegram_handler, "edit_telegram_message_reply_markup", AsyncMock()
    )

    asyncio.run(
        telegram_handler._handle_callback_query(
            MagicMock(), _cb_update("nav:back", message_id=701)
        )
    )

    send_patients.assert_awaited_once()
    _, kwargs = send_patients.await_args
    assert kwargs["page"] == 3
    assert kwargs["query"] == "maria"


def test_patient_actions_markup_includes_navigation_buttons():
    markup = telegram_handler._patient_actions_markup(9)
    flat_callbacks = [
        btn["callback_data"]
        for row in markup["inline_keyboard"]
        for btn in row
    ]
    assert "patient:diet:9" in flat_callbacks
    assert "patient:history:9:1" in flat_callbacks
    assert "nav:back" in flat_callbacks
    assert "nav:home" in flat_callbacks


def test_flow_back_from_note_offer_returns_to_patient_card(
    monkeypatch: pytest.MonkeyPatch,
):
    async def fake_doctor(db, uid: str):
        d = MagicMock()
        d.id = 1
        return d

    patient = MagicMock()
    patient.id = 5

    async def fake_load_state(db, doctor_id, key):
        return {
            "awaiting": "diet_note_offer",
            "patient_id": 5,
            "wizard_back_step": None,
        }

    async def fake_get_patient(db, doctor_id, patient_id):
        return patient if patient_id == 5 else None

    show_patient = AsyncMock()
    save_state = AsyncMock()
    answer_cb = AsyncMock()

    monkeypatch.setattr(telegram_handler, "_doctor_for_telegram_user", fake_doctor)
    monkeypatch.setattr(telegram_handler, "_load_state", fake_load_state)
    monkeypatch.setattr(telegram_handler, "get_doctor_patient", fake_get_patient)
    monkeypatch.setattr(telegram_handler, "_show_patient_card", show_patient)
    monkeypatch.setattr(telegram_handler, "_save_state", save_state)
    monkeypatch.setattr(telegram_handler, "answer_telegram_callback_query", answer_cb)

    asyncio.run(
        telegram_handler._handle_callback_query(
            MagicMock(), _cb_update("flow:back", message_id=701)
        )
    )

    show_patient.assert_awaited_once()
    save_state.assert_awaited_once()
    answer_cb.assert_awaited_once()


def test_wizard_note_offer_no_longer_shows_refresh_button():
    markup = telegram_diet_ui.diet_note_offer_markup(7)
    flat_callbacks = [
        btn["callback_data"]
        for row in markup["inline_keyboard"]
        for btn in row
    ]
    assert "flow:back" in flat_callbacks
    assert "flow:cancel" in flat_callbacks
    assert "flow:refresh" not in flat_callbacks


def test_edit_keyboards_include_preview_navigation():
    day_markup = telegram_handler._diet_edit_day_inline_keyboard(12, 7)
    day_callbacks = [
        btn["callback_data"]
        for row in day_markup["inline_keyboard"]
        for btn in row
    ]
    assert "diet:preview:resume:12" in day_callbacks

    slot_markup = telegram_handler._diet_edit_slot_inline_keyboard(
        12, 2, ["breakfast", "lunch"]
    )
    slot_callbacks = [
        btn["callback_data"]
        for row in slot_markup["inline_keyboard"]
        for btn in row
    ]
    assert "diet:preview:editpick:12" in slot_callbacks
    assert "diet:preview:resume:12" in slot_callbacks


def test_preview_resume_uses_preview_session_without_message_match(
    monkeypatch: pytest.MonkeyPatch,
):
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

    patient = MagicMock()
    patient.id = 3

    async def fake_load_state(db, doctor_id, key):
        return {
            "awaiting": "diet_preview",
            "pending_diet_id": 9,
            "patient_id": 3,
            "preview_message_id": 999,
        }

    async def mock_get(cls, did):
        return diet if did == 9 else None

    mock_db = MagicMock()
    mock_db.get = mock_get

    show_preview = AsyncMock()

    monkeypatch.setattr(telegram_handler, "_doctor_for_telegram_user", fake_doctor)
    monkeypatch.setattr(telegram_handler, "_load_state", fake_load_state)
    monkeypatch.setattr(
        telegram_handler, "get_doctor_patient", AsyncMock(return_value=patient)
    )
    monkeypatch.setattr(
        telegram_handler, "_send_diet_preview_and_store_state", show_preview
    )
    monkeypatch.setattr(
        telegram_handler, "answer_telegram_callback_query", AsyncMock()
    )
    monkeypatch.setattr(
        telegram_handler, "edit_telegram_message_reply_markup", AsyncMock()
    )

    asyncio.run(
        telegram_handler._handle_callback_query(
            mock_db, _cb_update("diet:preview:resume:9", message_id=222)
        )
    )

    show_preview.assert_awaited_once()


def test_manual_meal_edit_creates_audit_log(
    monkeypatch: pytest.MonkeyPatch,
):
    class FakeDB:
        def __init__(self, diet):
            self._diet = diet
            self.added = []

        async def get(self, cls, diet_id):
            return self._diet if diet_id == self._diet.id else None

        async def flush(self):
            return None

        def add(self, obj):
            self.added.append(obj)

    doctor = MagicMock()
    doctor.id = 1

    patient = MagicMock()
    patient.id = 3

    diet = MagicMock()
    diet.id = 9
    diet.doctor_id = 1
    diet.patient_id = 3
    diet.status = "pending_approval"
    diet.notes = ""
    diet.structured_plan_json = {
        "days": [
            {
                "day": 1,
                "meals": {
                    "breakfast": "Avena",
                    "lunch": "Pollo",
                },
            }
        ]
    }

    db = FakeDB(diet)

    state = {
        "pending_diet_id": 9,
        "edit_meal_day": 1,
        "edit_meal_slot_index": 0,
        "patient_id": 3,
    }

    monkeypatch.setattr(
        telegram_handler, "get_doctor_patient", AsyncMock(return_value=patient)
    )
    monkeypatch.setattr(telegram_handler, "_save_state", AsyncMock())
    monkeypatch.setattr(
        telegram_handler, "_format_diet_preview_message", lambda *a, **k: "preview"
    )
    monkeypatch.setattr(telegram_handler, "send_telegram_message", AsyncMock())

    result = asyncio.run(
        telegram_handler._handle_diet_tg_edit_meal_text(
            db,
            doctor,
            "100",
            "telegram:42",
            "Huevos y pan integral",
            state,
            "huevos y pan integral",
        )
    )

    assert result is True
    audit_rows = [
        row
        for row in db.added
        if isinstance(row, AuditLog) and row.action == "diet_edit_meal_manual"
    ]
    assert len(audit_rows) == 1
    payload = audit_rows[0].payload_json or {}
    assert payload.get("day") == 1
    assert payload.get("slot") == "breakfast"


def test_edit_day_picker_rejects_replaced_message(
    monkeypatch: pytest.MonkeyPatch,
):
    async def fake_doctor(db, uid: str):
        d = MagicMock()
        d.id = 1
        return d

    diet = MagicMock()
    diet.id = 9
    diet.doctor_id = 1
    diet.status = "pending_approval"

    async def fake_load_state(db, doctor_id, key):
        return {
            "awaiting": "diet_preview",
            "pending_diet_id": 9,
            "patient_id": 3,
            "edit_day_message_id": 888,
        }

    async def mock_get(cls, did):
        return diet if did == 9 else None

    mock_db = MagicMock()
    mock_db.get = mock_get

    stale_refresh = AsyncMock()
    send_message = AsyncMock()

    monkeypatch.setattr(telegram_handler, "_doctor_for_telegram_user", fake_doctor)
    monkeypatch.setattr(telegram_handler, "_load_state", fake_load_state)
    monkeypatch.setattr(
        telegram_handler, "_send_stale_step_refresh", stale_refresh
    )
    monkeypatch.setattr(telegram_handler, "send_telegram_message", send_message)
    monkeypatch.setattr(
        telegram_handler, "answer_telegram_callback_query", AsyncMock()
    )
    monkeypatch.setattr(
        telegram_handler, "edit_telegram_message_reply_markup", AsyncMock()
    )

    asyncio.run(
        telegram_handler._handle_callback_query(
            mock_db, _cb_update("diet:edday:9:1", message_id=701)
        )
    )

    stale_refresh.assert_awaited_once()
