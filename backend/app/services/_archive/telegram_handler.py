from __future__ import annotations

import copy
import inspect
import re
from typing import Any, Optional

from sqlalchemy import delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.logic.diet_duration import (
    DEFAULT_PLAN_DURATION_DAYS,
    DurationParseError,
    parse_duration_text,
    validate_duration_days,
)
from app.models import (
    AuditLog,
    ConversationState,
    Diet,
    Doctor,
    DoctorTelegramBinding,
    Patient,
    PatientMetrics,
    PatientProfile,
    TelegramPendingLink,
    utcnow,
)
from app.services.doctor_assistant_service import (
    add_patient_metric,
    doctor_diet_count,
    doctor_patient_stats,
    format_patient_summary,
    get_doctor_diet,
    get_doctor_patient,
    get_patient_profile,
    list_patient_diets,
    latest_metric,
    patient_identity_label,
    search_doctor_patients,
    update_patient_fields,
)
from app.services.measurement_parser import (
    measurement_in_reasonable_range,
    parse_height,
    parse_weight,
)
from app.services.telegram_intent_service import classify_intent_llm, rule_based_intent
from app.services.diet_export import build_diet_export_pdf_bytes
from app.services.plan_meals import (
    meal_slot_label_es,
    normalize_plan_meal_metadata,
    resolve_plan_meal_slots,
)
from app.services.telegram_diet_messages import (
    format_diet_preview_message as _format_diet_preview_message,
    format_telegram_full_day_block,
    split_telegram_text_chunks,
)
from app.services.telegram_diet_strategy import (
    STYLE_CODE_TO_API,
    diet_strategy_kwargs_from_state,
    strategy_summary_lines,
)
from app.services.telegram_diet_ui import (
    diet_confirm_body as _diet_confirm_body,
    diet_meals_choice_markup as _diet_meals_choice_markup,
    diet_meals_prompt_message as _diet_meals_prompt_message,
    diet_confirm_markup as _diet_confirm_markup,
    diet_duration_choice_markup as _diet_duration_choice_markup,
    diet_duration_prompt_message as _diet_duration_prompt_message,
    diet_macro_carbs_markup as _diet_macro_carbs_markup,
    diet_macro_carbs_prompt_message as _diet_macro_carbs_prompt_message,
    diet_macro_fat_markup as _diet_macro_fat_markup,
    diet_macro_fat_prompt_message as _diet_macro_fat_prompt_message,
    diet_macro_protein_markup as _diet_macro_protein_markup,
    diet_macro_protein_prompt_message as _diet_macro_protein_prompt_message,
    diet_manual_carbs_prompt_message as _diet_manual_carbs_prompt_message,
    diet_manual_fat_prompt_message as _diet_manual_fat_prompt_message,
    diet_manual_kcal_prompt_message as _diet_manual_kcal_prompt_message,
    diet_manual_protein_prompt_message as _diet_manual_protein_prompt_message,
    diet_note_offer_markup as _diet_note_offer_markup,
    diet_preview_markup as _diet_preview_markup,
    diet_regen_duration_choice_markup as _diet_regen_duration_choice_markup,
    diet_strategy_mode_markup as _diet_strategy_mode_markup,
    diet_strategy_mode_prompt_message as _diet_strategy_mode_prompt_message,
    diet_strategy_style_markup as _diet_strategy_style_markup,
    diet_strategy_style_prompt_message as _diet_strategy_style_prompt_message,
)
from app.services.diet_service import (
    DietGenerationError,
    approve_diet_preview,
    create_new_diet,
    discard_diet_preview,
    regenerate_diet,
)
from app.services.telegram_client import (
    answer_telegram_callback_query,
    edit_telegram_message_reply_markup,
    send_telegram_document,
    send_telegram_message,
)

PATIENTS_PAGE_SIZE = 6

# Claves de estado a persistir entre confirmación, métricas y bloqueos (modo nutricional Telegram).
_DIET_WIZARD_PERSIST_KEYS: tuple[str, ...] = (
    "meals_per_day",
    "strategy_mode",
    "diet_style",
    "macro_protein",
    "macro_carbs",
    "macro_fat",
    "manual_kcal",
    "manual_protein_g",
    "manual_carbs_g",
    "manual_fat_g",
    "strategy_flow",
    "pending_diet_id",
    "regen_instruction",
)


def _diet_wizard_persist_slice(state: dict) -> dict[str, Any]:
    return {k: state[k] for k in _DIET_WIZARD_PERSIST_KEYS if k in state}


def _diet_confirm_instruction_summary(st: dict) -> str:
    flow = st.get("strategy_flow", "new")
    if flow == "regen":
        raw = st.get("regen_instruction")
    else:
        raw = st.get("instruction")
    if isinstance(raw, str) and raw.strip():
        return raw.strip()
    return "(sin instrucción adicional)"


def _clear_guided_manual_fields(state: dict) -> None:
    for k in (
        "diet_style",
        "macro_protein",
        "macro_carbs",
        "macro_fat",
        "manual_kcal",
        "manual_protein_g",
        "manual_carbs_g",
        "manual_fat_g",
    ):
        state.pop(k, None)


# Códigos cortos para callback_data (máx. ~64 bytes en Telegram).
_DIET_QUICK_ADJUST: dict[str, tuple[str, str]] = {
    "more_prot": (
        "Más proteína",
        "Ajuste rápido: aumenta la proporción de proteína en el plan manteniendo variedad "
        "y respetando alergias y restricciones del paciente.",
    ),
    "less_cal": (
        "Menos calorías",
        "Ajuste rápido: reduce las calorías diarias del plan en torno a un 10–15 %, "
        "priorizando volumen con verduras y alimentos integrales.",
    ),
    "more_cal": (
        "Más calorías",
        "Ajuste rápido: incrementa las calorías diarias del plan en torno a un 10–15 % "
        "con alimentos nutritivos y bien tolerados.",
    ),
    "mediter": (
        "Estilo mediterráneo",
        "Ajuste rápido: orienta el plan hacia un patrón mediterráneo (verdura, legumbres, "
        "frutos secos, pescado, aceite de oliva virgen, cereales integrales).",
    ),
    "low_carb": (
        "Menos hidratos",
        "Ajuste rápido: reduce hidratos refinados o de acompañamiento en favor de verdura "
        "y proteína, sin restricción extrema.",
    ),
    "snack_add": (
        "Incluir snack",
        "Ajuste rápido: incorpora o refuerza una merienda/snack saludable entre comidas principales.",
    ),
    "snack_rm": (
        "Quitar snack",
        "Ajuste rápido: elimina la merienda/snack y redistribuye la ingesta en desayuno, comida y cena.",
    ),
    "less_ultra": (
        "Menos ultraprocesados",
        "Ajuste rápido: reduce ultraprocesados y fritos; prioriza alimentos frescos y preparación casera simple.",
    ),
}


def _merge_note_with_quick_adjust(
    existing_note: Optional[str],
    quick_key: str,
) -> str:
    meta = _DIET_QUICK_ADJUST.get(quick_key)
    if not meta:
        return (existing_note or "").strip()
    _, snippet = meta
    base = (existing_note or "").strip()
    if base:
        return f"{base}\n\n{snippet}"
    return snippet


def _diet_quick_adjust_markup(diet_id: int) -> dict:
    rows: list[list[dict]] = []
    pair: list[dict] = []
    for code, (label, _) in _DIET_QUICK_ADJUST.items():
        pair.append(
            {
                "text": label,
                "callback_data": f"diet:quick:{code}:{diet_id}",
            }
        )
        if len(pair) == 2:
            rows.append(pair)
            pair = []
    if pair:
        rows.append(pair)
    rows.append(
        [
            {
                "text": "« Volver a la vista previa",
                "callback_data": f"diet:preview:reshow:{diet_id}",
            }
        ]
    )
    return {"inline_keyboard": rows}

INTENT_POLICY: dict[str, str] = {
    "greeting": "safe",
    "thanks": "safe",
    "menu": "safe",
    "help": "safe",
    "search": "safe",
    "patients": "safe",
    "stats_patients": "safe",
    "stats_diets": "safe",
    "stats_summary": "safe",
    "diet": "guided_diet",
    "patient_history": "needs_patient",
    "patient_show": "needs_patient",
    "patient_edit": "needs_patient",
    "possible_mutation": "needs_patient",
    "unknown": "unmapped",
}

MSG_NO_DATA = "No tengo ese dato en el sistema todavía."


async def _doctor_for_telegram_user(
    db: AsyncSession, telegram_user_id: str
) -> Optional[Doctor]:
    result = await db.execute(
        select(DoctorTelegramBinding).where(
            DoctorTelegramBinding.telegram_user_id == telegram_user_id,
            DoctorTelegramBinding.is_active.is_(True),
        )
    )
    binding = result.scalar_one_or_none()
    if binding is None:
        return None
    return await db.get(Doctor, binding.doctor_id)


async def _latest_metric(
    db: AsyncSession, patient_id: int
) -> Optional[PatientMetrics]:
    result = await db.execute(
        select(PatientMetrics)
        .where(PatientMetrics.patient_id == patient_id)
        .order_by(PatientMetrics.recorded_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def _resolve_patient_for_doctor(
    db: AsyncSession, doctor: Doctor, q: str
) -> tuple[Optional[Patient], Optional[str], Optional[list[Patient]]]:
    q = q.strip()
    if not q:
        return None, "Indica nombre, apellido o número de paciente.", None
    if q.isdigit():
        patient = await db.get(Patient, int(q))
        if patient is None or patient.doctor_id != doctor.id:
            return None, "No encontré ese paciente.", None
        return patient, None, None
    term = f"%{q.lower()}%"
    result = await db.execute(
        select(Patient)
        .where(
            Patient.doctor_id == doctor.id,
            Patient.is_archived.is_(False),
            or_(
                func.lower(
                    func.concat(Patient.first_name, " ", Patient.last_name)
                ).like(term),
                func.lower(Patient.first_name).like(term),
                func.lower(Patient.last_name).like(term),
            ),
        )
        .limit(5)
    )
    rows = list(result.scalars().all())
    if not rows:
        return None, "No encontré un paciente con ese nombre.", None
    if len(rows) > 1:
        return None, None, rows
    return rows[0], None, None


def _extract_diet_patient_hint(text: str) -> str:
    t = text.strip()
    if not t:
        return t
    m = re.search(r"\b(?:para|de|del|paciente)\s+(\S+)", t, re.I)
    if m:
        return m.group(1).strip(".,;:!?")
    skip = {
        "una",
        "un",
        "dieta",
        "dietas",
        "plan",
        "quiero",
        "genera",
        "generar",
        "hacer",
        "crear",
        "para",
        "con",
        "sin",
        "los",
        "las",
        "dias",
        "días",
        "día",
        "dia",
    }
    for word in re.findall(r"\b\w+\b", t, flags=re.UNICODE):
        if word.lower() not in skip and len(word) >= 3:
            return word
    return ""


async def _send_diet_pdf(
    db: AsyncSession,
    doctor: Doctor,
    chat_id: str,
    diet: Diet,
    *,
    patient: Optional[Patient] = None,
) -> None:
    if diet.doctor_id != doctor.id:
        await send_telegram_message(chat_id, "No tienes acceso a esa dieta.")
        return
    patient = patient or await db.get(Patient, diet.patient_id)
    if patient is None or patient.doctor_id != doctor.id:
        await send_telegram_message(chat_id, "Paciente no encontrado para esa dieta.")
        return

    pr_result = await db.execute(
        select(PatientProfile).where(PatientProfile.patient_id == patient.id)
    )
    profile = pr_result.scalar_one_or_none()
    latest = await _latest_metric(db, patient.id)
    pdf_bytes = build_diet_export_pdf_bytes(
        diet,
        patient=patient,
        profile=profile,
        metrics=latest,
        doctor=doctor,
    )
    safe_name = f"{patient.first_name}_{patient.last_name}".replace(" ", "_")
    await send_telegram_document(
        chat_id,
        pdf_bytes,
        filename=f"dieta_{diet.id}_{safe_name}.pdf",
        caption=f"Dieta #{diet.id} lista para compartir.",
    )


async def _complete_bind(
    db: AsyncSession, code: str, from_user: dict, chat_id: str
) -> tuple[bool, str]:
    result = await db.execute(
        select(TelegramPendingLink).where(TelegramPendingLink.code == code)
    )
    pending = result.scalar_one_or_none()
    now = utcnow()
    if pending is None or pending.expires_at < now:
        return (
            False,
            "Enlace de vinculación inválido o caducado. En el panel: Telegram → "
            "«Generate link» y abre el nuevo enlace en este chat (o revisa que no queden "
            "espacios al copiar el código).",
        )

    doctor = await db.get(Doctor, pending.doctor_id)
    if doctor is None or not doctor.is_active:
        return False, "Doctor account not available."

    uid = str(from_user["id"])
    await db.execute(
        delete(DoctorTelegramBinding).where(
            DoctorTelegramBinding.telegram_user_id == uid
        )
    )
    await db.execute(
        delete(DoctorTelegramBinding).where(
            DoctorTelegramBinding.telegram_chat_id == str(chat_id)
        )
    )

    binding = DoctorTelegramBinding(
        doctor_id=doctor.id,
        telegram_user_id=uid,
        telegram_chat_id=str(chat_id),
        telegram_username=from_user.get("username"),
    )
    db.add(binding)
    doctor.telegram_user_id = uid
    doctor.telegram_username = from_user.get("username")
    doctor.updated_at = now

    db.add(
        AuditLog(
            doctor_id=doctor.id,
            action="telegram_bind",
            entity_type="doctor_telegram_binding",
            entity_id=None,
            payload_json={"telegram_user_id": uid},
        )
    )
    await db.execute(
        delete(ConversationState).where(
            ConversationState.doctor_id == doctor.id,
            ConversationState.channel_user_key == f"telegram:{uid}",
        )
    )
    return (
        True,
        "Telegram vinculado a tu cuenta de doctor/a.",
    )


def _doctor_greeting_name(doctor: Doctor) -> str:
    name = (doctor.full_name or "").strip()
    if not name:
        return "Doctora"
    return name.split()[0] if name.split() else name


def _welcome_extended_block(doctor: Doctor) -> str:
    who = _doctor_greeting_name(doctor)
    return (
        f"Hola, {who}. Bienvenida al asistente del consultorio.\n\n"
        "Desde aquí puedes ver pacientes, estadísticas y generar dietas con confirmación. "
        "También puedes escribir en lenguaje natural.\n\n"
        "Usa el menú inferior o prueba por ejemplo: «quiero ver mis pacientes» o "
        "«genera una dieta para Maria»."
    )


HELP_TEXT = (
    "Asistente del consultorio:\n"
    "• Abre el menú para ver pacientes y estadísticas.\n"
    "• Selecciona un paciente para generar dieta, ver historial y actualizar datos.\n"
    "• Al generar o regenerar un borrador te pediré la duración total en días (múltiplos de 7); "
    "puedes usar los botones rápidos o escribir el número o las semanas.\n"
    "• Puedes escribir en lenguaje natural, por ejemplo:\n"
    "  - 'quiero ver mis pacientes'\n"
    "  - 'genera una dieta para Carlos'\n"
    "• Escribe 'cancelar' para salir de cualquier flujo y volver al menú."
)

MSG_NO_DIETA_CMD = (
    "Para generar una dieta: "
    "Abre «Pacientes» en el menú, elige a alguien y «Generar dieta», "
    "o escribe por ejemplo: «genera una dieta para Maria»."
)

MSG_NO_PDF_CMD = (
    "Para obtener el PDF: "
    "Entra al paciente → «Historial dietas» y pulsa el botón de la dieta que quieras."
)

MSG_PANEL_ONLY_UPDATES = (
    "Esta acción solo está disponible en el panel web. "
    "Abre el paciente en el panel para actualizar ese dato."
)


async def _load_state(db: AsyncSession, doctor_id: int, channel_user_key: str) -> dict:
    return await _load_state_with_lock(
        db, doctor_id, channel_user_key, for_update=False
    )


async def _load_state_with_lock(
    db: AsyncSession,
    doctor_id: int,
    channel_user_key: str,
    *,
    for_update: bool,
) -> dict:
    stmt = select(ConversationState).where(
        ConversationState.doctor_id == doctor_id,
        ConversationState.channel_user_key == channel_user_key,
    )
    if for_update:
        stmt = stmt.with_for_update()
    result = await db.execute(stmt)
    row = result.scalar_one_or_none()
    if not row or not isinstance(row.context_data, dict):
        return {}
    return dict(row.context_data)


async def _load_state_for_update(
    db: AsyncSession, doctor_id: int, channel_user_key: str
) -> dict:
    try:
        return await _load_state_with_lock(
            db, doctor_id, channel_user_key, for_update=True
        )
    except TypeError:
        # Test doubles may not implement awaitable db.execute(); fall back to plain load.
        return await _load_state(db, doctor_id, channel_user_key)


def _callback_message_id(message: dict[str, Any]) -> int | None:
    mid = message.get("message_id")
    return mid if isinstance(mid, int) else None


def _state_message_matches(
    state: dict[str, Any],
    *,
    key: str,
    message: dict[str, Any],
) -> bool:
    expected = state.get(key)
    if expected is None:
        return True
    return isinstance(expected, int) and expected == _callback_message_id(message)


def _drop_state_keys(state: dict[str, Any], *keys: str) -> dict[str, Any]:
    out = dict(state)
    for key in keys:
        out.pop(key, None)
    return out


async def _send_diet_confirm_prompt(
    db: AsyncSession,
    doctor: Doctor,
    chat_id: str,
    channel_user_key: str,
    patient: Patient,
    *,
    body: str,
) -> None:
    mid = await send_telegram_message(
        chat_id,
        body,
        reply_markup=_diet_confirm_markup(patient.id),
    )
    payload: dict[str, Any] = {
        "confirm_message_id": mid,
        "wizard_inline_message_id": None,
    }
    if mid is None:
        payload["confirm_message_id"] = None
    await _save_state(db, doctor.id, channel_user_key, payload)


async def _send_diet_preview_and_store_state(
    db: AsyncSession,
    doctor: Doctor,
    chat_id: str,
    channel_user_key: str,
    diet: Diet,
    patient: Patient,
    *,
    doctor_note: Optional[str],
) -> None:
    preview = _format_diet_preview_message(
        diet, patient, doctor_note=doctor_note
    )
    mid = await send_telegram_message(
        chat_id,
        preview,
        reply_markup=_diet_preview_markup(diet.id),
    )
    await _save_state(
        db,
        doctor.id,
        channel_user_key,
        {
            "awaiting": "diet_preview",
            "pending_diet_id": diet.id,
            "patient_id": patient.id,
            "preview_message_id": mid,
            "quick_adjust_message_id": None,
            "confirm_message_id": None,
            "wizard_inline_message_id": None,
            "wizard_back_step": None,
            "edit_day_message_id": None,
            "edit_slot_message_id": None,
        },
    )


async def _send_wizard_inline_prompt(
    db: AsyncSession,
    doctor: Doctor,
    chat_id: str,
    channel_user_key: str,
    *,
    text: str,
    reply_markup: dict[str, Any],
    state_patch: Optional[dict[str, Any]] = None,
) -> None:
    mid = await send_telegram_message(
        chat_id,
        text,
        reply_markup=reply_markup,
    )
    payload: dict[str, Any] = {
        "wizard_inline_message_id": mid,
        "confirm_message_id": None,
    }
    if state_patch:
        payload = {**state_patch, **payload}
    await _save_state(
        db,
        doctor.id,
        channel_user_key,
        payload,
    )


async def _send_diet_quick_adjust_menu(
    db: AsyncSession,
    doctor: Doctor,
    chat_id: str,
    channel_user_key: str,
    diet_id: int,
) -> None:
    mid = await send_telegram_message(
        chat_id,
        "Elige un ajuste rápido. Se regenerará el plan con ese cambio "
        "(se conserva tu nota clínica previa cuando aplica).",
        reply_markup=_diet_quick_adjust_markup(diet_id),
    )
    await _save_state(
        db,
        doctor.id,
        channel_user_key,
        {"quick_adjust_message_id": mid},
    )

async def _save_state(
    db: AsyncSession, doctor_id: int, channel_user_key: str, data: dict
) -> None:
    prev = await _load_state(db, doctor_id, channel_user_key)
    merged = {**prev, **data}
    execute = getattr(db, "execute", None)
    if not callable(execute) or not inspect.iscoroutinefunction(execute):
        return
    result = await db.execute(
        select(ConversationState).where(
            ConversationState.doctor_id == doctor_id,
            ConversationState.channel_user_key == channel_user_key,
        )
    )
    row = result.scalar_one_or_none()
    if row is None:
        row = ConversationState(
            doctor_id=doctor_id,
            channel_user_key=channel_user_key,
            context_data=merged,
            updated_at=utcnow(),
        )
        db.add(row)
        return
    row.context_data = merged
    row.updated_at = utcnow()


async def _clear_state(db: AsyncSession, doctor_id: int, channel_user_key: str) -> None:
    prev = await _load_state(db, doctor_id, channel_user_key)
    keep_data = {
        "welcome_shown": prev.get("welcome_shown"),
        "last_active_patient_id": prev.get("last_active_patient_id"),
        "active_patient_id": prev.get("active_patient_id"),
    }
    await db.execute(
        delete(ConversationState).where(
            ConversationState.doctor_id == doctor_id,
            ConversationState.channel_user_key == channel_user_key,
        )
    )
    keep_data = {k: v for k, v in keep_data.items() if v}
    if keep_data:
        await _save_state(db, doctor_id, channel_user_key, keep_data)


async def _remember_patient_context(
    db: AsyncSession, doctor_id: int, channel_user_key: str, patient_id: int
) -> None:
    await _save_state(
        db,
        doctor_id,
        channel_user_key,
        {
            "last_active_patient_id": patient_id,
            "active_patient_id": patient_id,
        },
    )


def _preview_session_matches(state: dict, diet_id: int) -> bool:
    return state.get("awaiting") == "diet_preview" and state.get(
        "pending_diet_id"
    ) == diet_id


# Pasos del asistente de dieta (mismo paciente): bloquear relanzar «Generar dieta».
_ACTIVE_DIET_WIZARD_AWAITING: frozenset[str] = frozenset(
    {
        "diet_note_offer",
        "diet_duration",
        "diet_instruction",
        "diet_meals_per_day",
        "diet_strategy_mode",
        "diet_strategy_style",
        "diet_macro_protein",
        "diet_macro_carbs",
        "diet_macro_fat",
        "diet_manual_kcal",
        "diet_manual_protein_g",
        "diet_manual_carbs_g",
        "diet_manual_fat_g",
        "diet_confirm",
        "diet_preview",
        "diet_regenerate_duration",
        "diet_regenerate_note",
        "diet_tg_edit_meal",
    }
)


def _has_active_diet_wizard_for_patient(state: dict, patient_id: int) -> bool:
    aw = state.get("awaiting")
    if aw not in _ACTIVE_DIET_WIZARD_AWAITING:
        return False
    pid = state.get("patient_id")
    return isinstance(pid, int) and pid == patient_id


def _patient_switch_confirm_markup(
    action: str, patient_id: int, extra: str
) -> dict:
    safe_extra = extra if extra else "_"
    return {
        "inline_keyboard": [
            [
                {
                    "text": "Sí",
                    "callback_data": f"flow:pswitch:yes:{action}:{patient_id}:{safe_extra}",
                },
                {"text": "No", "callback_data": "flow:pswitch:no"},
            ]
        ]
    }


async def _send_stale_step_refresh(
    db: AsyncSession,
    doctor: Doctor,
    chat_id: str,
    channel_user_key: str,
    *,
    prefix: str = "Este paso ya no aplica.",
) -> None:
    state = await _load_state(db, doctor.id, channel_user_key)
    awaiting = state.get("awaiting")
    patient_id = state.get("patient_id")
    pending_diet_id = state.get("pending_diet_id")
    if awaiting == "diet_preview" and isinstance(pending_diet_id, int):
        diet = await get_doctor_diet(db, doctor.id, pending_diet_id)
        patient = None
        if diet:
            patient = await get_doctor_patient(db, doctor.id, diet.patient_id)
        if diet and patient:
            await _send_diet_preview_and_store_state(
                db,
                doctor,
                chat_id,
                channel_user_key,
                diet,
                patient,
                doctor_note=diet.notes,
            )
            return
        await send_telegram_message(
            chat_id,
            f"{prefix} Te muestro la vista previa vigente.",
            reply_markup=_diet_preview_markup(pending_diet_id),
        )
        return
    if awaiting == "diet_note_offer" and isinstance(patient_id, int):
        default_note = (
            "¿Quieres agregar una nota o especificaciones extra para orientar la generación "
            "de la dieta? Es opcional."
        )
        body = prefix.strip() if prefix.strip() else default_note
        await _send_wizard_inline_prompt(
            db,
            doctor,
            chat_id,
            channel_user_key,
            text=body,
            reply_markup=_diet_note_offer_markup(patient_id),
        )
        return
    if awaiting == "diet_duration" and isinstance(patient_id, int):
        await _send_wizard_inline_prompt(
            db,
            doctor,
            chat_id,
            channel_user_key,
            text=f"{prefix} Continúa con la duración.",
            reply_markup=_diet_duration_choice_markup(patient_id),
        )
        return
    if awaiting == "diet_regenerate_duration" and isinstance(pending_diet_id, int):
        await _send_wizard_inline_prompt(
            db,
            doctor,
            chat_id,
            channel_user_key,
            text=f"{prefix} Indica de nuevo la duración del plan.",
            reply_markup=_diet_regen_duration_choice_markup(pending_diet_id),
        )
        return
    if awaiting == "diet_meals_per_day" and isinstance(patient_id, int):
        await _send_wizard_inline_prompt(
            db,
            doctor,
            chat_id,
            channel_user_key,
            text=f"{prefix} Continúa con comidas por día.",
            reply_markup=_diet_meals_choice_markup(patient_id),
        )
        return
    if awaiting == "diet_strategy_mode" and isinstance(patient_id, int):
        await _send_wizard_inline_prompt(
            db,
            doctor,
            chat_id,
            channel_user_key,
            text=f"{prefix} Continúa con el modo nutricional.",
            reply_markup=_diet_strategy_mode_markup(patient_id),
        )
        return
    if awaiting == "diet_strategy_style" and isinstance(patient_id, int):
        await _send_wizard_inline_prompt(
            db,
            doctor,
            chat_id,
            channel_user_key,
            text=f"{prefix} Continúa con el estilo de dieta.",
            reply_markup=_diet_strategy_style_markup(patient_id),
        )
        return
    if awaiting == "diet_confirm" and isinstance(patient_id, int):
        patient = await get_doctor_patient(db, doctor.id, patient_id)
        if patient:
            await _send_diet_confirm_prompt(
                db,
                doctor,
                chat_id,
                channel_user_key,
                patient,
                body=f"{prefix} Usa los botones de confirmación vigentes abajo.",
            )
        else:
            await send_telegram_message(chat_id, prefix, reply_markup=_menu_markup())
        return
    if awaiting in {
        "diet_instruction",
        "diet_regenerate_note",
        "diet_edit_text",
        "diet_tg_edit_meal",
        "search_query",
    }:
        await send_telegram_message(
            chat_id,
            f"{prefix} Continúa desde el paso actual.",
            reply_markup=_cancel_markup(),
        )
        return
    if awaiting == "diet_macro_protein":
        await _send_wizard_inline_prompt(
            db,
            doctor,
            chat_id,
            channel_user_key,
            text=f"{prefix} Continúa con la proteína del plan.",
            reply_markup=_diet_macro_protein_markup(),
        )
        return
    if awaiting == "diet_macro_carbs":
        await _send_wizard_inline_prompt(
            db,
            doctor,
            chat_id,
            channel_user_key,
            text=f"{prefix} Continúa con los hidratos del plan.",
            reply_markup=_diet_macro_carbs_markup(),
        )
        return
    if awaiting == "diet_macro_fat":
        await _send_wizard_inline_prompt(
            db,
            doctor,
            chat_id,
            channel_user_key,
            text=f"{prefix} Continúa con las grasas del plan.",
            reply_markup=_diet_macro_fat_markup(),
        )
        return
    if awaiting == "diet_manual_kcal":
        await send_telegram_message(
            chat_id,
            (f"{prefix} " if prefix else "")
            + _diet_manual_kcal_prompt_message(),
            reply_markup=_cancel_markup(),
        )
        return
    if awaiting == "diet_manual_protein_g":
        await send_telegram_message(
            chat_id,
            (f"{prefix} " if prefix else "")
            + _diet_manual_protein_prompt_message(),
            reply_markup=_cancel_markup(),
        )
        return
    if awaiting == "diet_manual_carbs_g":
        await send_telegram_message(
            chat_id,
            (f"{prefix} " if prefix else "")
            + _diet_manual_carbs_prompt_message(),
            reply_markup=_cancel_markup(),
        )
        return
    if awaiting == "diet_manual_fat_g":
        await send_telegram_message(
            chat_id,
            (f"{prefix} " if prefix else "")
            + _diet_manual_fat_prompt_message(),
            reply_markup=_cancel_markup(),
        )
        return
    await send_telegram_message(chat_id, prefix, reply_markup=_menu_markup())


async def _guard_active_patient_switch(
    db: AsyncSession,
    doctor: Doctor,
    chat_id: str,
    channel_user_key: str,
    *,
    target_patient_id: int,
    action: str,
    extra: str = "_",
) -> bool:
    state = await _load_state(db, doctor.id, channel_user_key)
    active = state.get("active_patient_id")
    if not isinstance(active, int) or active == target_patient_id:
        return True
    target = await get_doctor_patient(db, doctor.id, target_patient_id)
    if not target:
        await send_telegram_message(chat_id, "Paciente no encontrado.")
        return False
    await _save_state(
        db,
        doctor.id,
        channel_user_key,
        {
            "pending_switch_patient_id": target_patient_id,
            "pending_switch_action": action,
            "pending_switch_extra": extra,
        },
    )
    await send_telegram_message(
        chat_id,
        f"Actualmente trabajas con otro paciente. ¿Confirmar cambio a {target.first_name} {target.last_name}?",
        reply_markup=_patient_switch_confirm_markup(
            action, target_patient_id, extra
        ),
    )
    return False


async def _try_strip_callback_inline_keyboard(
    chat_id: str, message: dict[str, Any]
) -> None:
    mid = message.get("message_id")
    if not isinstance(mid, int):
        return
    await edit_telegram_message_reply_markup(chat_id, mid, reply_markup=None)


async def _last_active_patient(
    db: AsyncSession, doctor: Doctor, channel_user_key: str
) -> Optional[Patient]:
    state = await _load_state(db, doctor.id, channel_user_key)
    patient_id = state.get("last_active_patient_id")
    if not isinstance(patient_id, int):
        return None
    return await get_doctor_patient(db, doctor.id, patient_id)


def _menu_markup() -> dict:
    return {
        "inline_keyboard": [
            [
                {"text": "Pacientes", "callback_data": "menu:patients:1"},
                {"text": "Estadísticas", "callback_data": "menu:stats"},
            ],
            [{"text": "Ayuda", "callback_data": "menu:help"}],
        ]
    }


def _cancel_markup() -> dict:
    return {
        "inline_keyboard": [[{"text": "Cancelar", "callback_data": "flow:cancel"}]]
    }


def _navigation_callback_requires_fresh_message(data: str) -> bool:
    return (
        data.startswith("menu:")
        or data.startswith("patient:")
        or data.startswith("nav:")
    )


def _should_strip_inline_after_callback(data: str) -> bool:
    return (
        data.startswith("nav:")
        or data.startswith("menu:")
        or data.startswith("patient:")
        or data.startswith("diet:")
        or data.startswith("flow:pswitch")
    )


def _navigation_footer_markup(
    *,
    include_back: bool = True,
    home_label: str = "Inicio",
) -> list[list[dict[str, str]]]:
    rows: list[list[dict[str, str]]] = []
    if include_back:
        rows.append(
            [
                {"text": "⬅ Volver", "callback_data": "nav:back"},
                {"text": home_label, "callback_data": "nav:home"},
            ]
        )
    else:
        rows.append([{"text": home_label, "callback_data": "nav:home"}])
    return rows


def _navigation_back_state(
    screen: str | None,
    *,
    patient_id: int | None = None,
    page: int | None = None,
    query: str | None = None,
) -> dict[str, Any]:
    return {
        "navigation_back_screen": screen,
        "navigation_back_patient_id": patient_id,
        "navigation_back_page": page,
        "navigation_back_query": query,
    }


def _navigation_back_state_from_context(state: dict[str, Any]) -> dict[str, Any]:
    return _navigation_back_state(
        state.get("navigation_back_screen")
        if isinstance(state.get("navigation_back_screen"), str)
        else None,
        patient_id=state.get("navigation_back_patient_id")
        if isinstance(state.get("navigation_back_patient_id"), int)
        else None,
        page=state.get("navigation_back_page")
        if isinstance(state.get("navigation_back_page"), int)
        else None,
        query=state.get("navigation_back_query")
        if isinstance(state.get("navigation_back_query"), str)
        else None,
    )


def _navigation_current_state(state: dict[str, Any]) -> dict[str, Any]:
    return _navigation_back_state(
        state.get("navigation_screen")
        if isinstance(state.get("navigation_screen"), str)
        else None,
        patient_id=state.get("navigation_patient_id")
        if isinstance(state.get("navigation_patient_id"), int)
        else None,
        page=state.get("navigation_page")
        if isinstance(state.get("navigation_page"), int)
        else None,
        query=state.get("navigation_query")
        if isinstance(state.get("navigation_query"), str)
        else None,
    )


async def _send_navigation_message(
    db: AsyncSession,
    doctor: Doctor,
    chat_id: str,
    channel_user_key: str,
    *,
    screen: str,
    text: str,
    reply_markup: dict[str, Any] | None = None,
    state_patch: Optional[dict[str, Any]] = None,
    back_state: Optional[dict[str, Any]] = None,
) -> None:
    mid = await send_telegram_message(chat_id, text, reply_markup=reply_markup)
    payload: dict[str, Any] = {
        "navigation_screen": screen,
        "navigation_message_id": mid,
    }
    payload.update(
        back_state
        if back_state is not None
        else _navigation_back_state(None)
    )
    if state_patch:
        payload.update(state_patch)
    await _save_state(db, doctor.id, channel_user_key, payload)


async def _send_home_screen(
    db: AsyncSession,
    doctor: Doctor,
    chat_id: str,
    channel_user_key: str,
    *,
    prefix: str | None = None,
) -> None:
    text = _welcome_extended_block(doctor)
    if prefix:
        text = f"{prefix}\n\n{text}"
    await _send_navigation_message(
        db,
        doctor,
        chat_id,
        channel_user_key,
        screen="home",
        text=text,
        reply_markup=_menu_markup(),
        state_patch={
            "navigation_patient_id": None,
            "navigation_page": None,
            "navigation_query": None,
        },
    )


async def _send_help_screen(
    db: AsyncSession,
    doctor: Doctor,
    chat_id: str,
    channel_user_key: str,
    *,
    prefix: str | None = None,
) -> None:
    text = HELP_TEXT if not prefix else f"{prefix}\n\n{HELP_TEXT}"
    await _send_navigation_message(
        db,
        doctor,
        chat_id,
        channel_user_key,
        screen="help",
        text=text,
        reply_markup=_menu_markup(),
        state_patch={
            "navigation_patient_id": None,
            "navigation_page": None,
            "navigation_query": None,
        },
    )


async def _send_stats_screen(
    db: AsyncSession,
    doctor: Doctor,
    chat_id: str,
    channel_user_key: str,
    *,
    prefix: str | None = None,
) -> None:
    stats = await doctor_patient_stats(db, doctor.id)
    diet_total = await doctor_diet_count(db, doctor.id)
    first = stats.get("first_patient")
    last = stats.get("last_patient")
    lines = [
        f"Total pacientes: {stats['total']}",
        f"Total dietas generadas: {diet_total}",
    ]
    if first:
        lines.append(f"Primer paciente: {patient_identity_label(first)}")
    if last:
        lines.append(f"Último paciente: {patient_identity_label(last)}")
    text = "\n".join(lines)
    if prefix:
        text = f"{prefix}\n\n{text}"
    await _send_navigation_message(
        db,
        doctor,
        chat_id,
        channel_user_key,
        screen="stats",
        text=text,
        reply_markup=_menu_markup(),
        state_patch={
            "navigation_patient_id": None,
            "navigation_page": None,
            "navigation_query": None,
        },
    )


async def _send_stale_navigation_refresh(
    db: AsyncSession,
    doctor: Doctor,
    chat_id: str,
    channel_user_key: str,
    *,
    prefix: str = "Esa pantalla ya fue reemplazada.",
) -> None:
    state = await _load_state(db, doctor.id, channel_user_key)
    back_state = _navigation_back_state_from_context(state)
    screen = state.get("navigation_screen")
    if screen == "help":
        await _send_help_screen(
            db, doctor, chat_id, channel_user_key, prefix=prefix
        )
        return
    if screen == "stats":
        await _send_stats_screen(
            db, doctor, chat_id, channel_user_key, prefix=prefix
        )
        return
    if screen == "patients":
        page = state.get("navigation_page")
        query = state.get("navigation_query")
        await _send_patients_page(
            db,
            doctor,
            chat_id,
            channel_user_key,
            page=page if isinstance(page, int) else 1,
            query=query if isinstance(query, str) and query else None,
            prefix=prefix,
        )
        return
    if screen == "patient_picker":
        picker_ids = state.get("navigation_picker_patient_ids")
        header = state.get("navigation_picker_header")
        if isinstance(picker_ids, list):
            rows: list[Patient] = []
            for raw_pid in picker_ids:
                if not isinstance(raw_pid, int):
                    continue
                patient = await get_doctor_patient(db, doctor.id, raw_pid)
                if patient:
                    rows.append(patient)
            if rows:
                await _send_ambiguous_patient_buttons(
                    db,
                    doctor,
                    chat_id,
                    channel_user_key,
                    rows,
                    header=header
                    if isinstance(header, str) and header.strip()
                    else "Varios pacientes coinciden. Elige uno:",
                    prefix=prefix,
                    back_state=back_state,
                )
                return
    if screen in {"patient_card", "patient_history"}:
        patient_id = state.get("navigation_patient_id")
        if isinstance(patient_id, int):
            patient = await get_doctor_patient(db, doctor.id, patient_id)
            if patient:
                if screen == "patient_history":
                    page = state.get("navigation_page")
                    await _send_patient_history_ui(
                        db,
                        doctor,
                        chat_id,
                        patient_id,
                        channel_user_key=channel_user_key,
                        page=page if isinstance(page, int) else 1,
                        prefix=prefix,
                        back_state=back_state,
                    )
                    return
                await _show_patient_card(
                    db,
                    doctor,
                    chat_id,
                    channel_user_key,
                    patient,
                    prefix=prefix,
                    back_state=back_state,
                )
                return
    await _send_home_screen(
        db, doctor, chat_id, channel_user_key, prefix=prefix
    )


async def _send_navigation_back_target(
    db: AsyncSession,
    doctor: Doctor,
    chat_id: str,
    channel_user_key: str,
    state: dict[str, Any],
    *,
    prefix: str,
) -> None:
    back_screen = state.get("navigation_back_screen")
    back_page = state.get("navigation_back_page")
    back_query = state.get("navigation_back_query")
    back_patient_id = state.get("navigation_back_patient_id")
    if back_screen == "patients":
        await _send_patients_page(
            db,
            doctor,
            chat_id,
            channel_user_key,
            page=back_page if isinstance(back_page, int) else 1,
            query=back_query if isinstance(back_query, str) and back_query else None,
            prefix=prefix,
        )
        return
    if back_screen == "patient_card" and isinstance(back_patient_id, int):
        patient = await get_doctor_patient(db, doctor.id, back_patient_id)
        if patient:
            parent_state = _navigation_back_state(
                "patients",
                page=state.get("navigation_page")
                if isinstance(state.get("navigation_page"), int)
                else 1,
                query=state.get("navigation_query")
                if isinstance(state.get("navigation_query"), str)
                else None,
            )
            await _show_patient_card(
                db,
                doctor,
                chat_id,
                channel_user_key,
                patient,
                prefix=prefix,
                back_state=parent_state,
            )
            return
    await _send_home_screen(
        db, doctor, chat_id, channel_user_key, prefix=prefix
    )


_DIET_TG_MEAL_TEXT_MAX = 3500


def _diet_edit_day_inline_keyboard(diet_id: int, num_days: int) -> dict:
    # Máx. 14 días en botones (límite práctico de filas; planes más largos: elige por tramos o edita vía web).
    n = min(max(1, num_days), 14)
    day_buttons: list[dict] = [
        {
            "text": str(d),
            "callback_data": f"diet:edday:{diet_id}:{d}",
        }
        for d in range(1, n + 1)
    ]
    row_size = 4
    grid = [
        day_buttons[i : i + row_size] for i in range(0, len(day_buttons), row_size)
    ]
    grid.append(
        [
            {
                "text": "Volver al resumen",
                "callback_data": f"diet:preview:resume:{diet_id}",
            }
        ]
    )
    return {"inline_keyboard": grid}


def _diet_edit_slot_inline_keyboard(
    diet_id: int, day_1: int, slot_keys: list[str]
) -> dict:
    rows: list[list[dict]] = []
    row: list[dict] = []
    for i, slot in enumerate(slot_keys):
        short = (
            "Des" if slot == "breakfast" else
            "MM" if slot == "mid_morning_snack" else
            "A" if slot == "lunch" else
            "M" if slot == "snack" else
            "Ce" if slot == "dinner" else
            meal_slot_label_es(slot)[:10]
        )
        row.append(
            {
                "text": f"{i + 1}. {short}",
                "callback_data": f"diet:edsl:{diet_id}:{day_1}:{i}",
            }
        )
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append(
        [
            {
                "text": "⬅ Dias",
                "callback_data": f"diet:preview:editpick:{diet_id}",
            },
            {
                "text": "Resumen",
                "callback_data": f"diet:preview:resume:{diet_id}",
            },
        ]
    )
    return {"inline_keyboard": rows}


async def _transition_new_diet_duration_to_strategy(
    db: AsyncSession,
    doctor: Doctor,
    chat_id: str,
    channel_user_key: str,
    patient: Patient,
    instruction: Optional[str],
    ddays: int,
) -> None:
    try:
        ddays = validate_duration_days(ddays)
    except ValueError as e:
        await send_telegram_message(
            chat_id,
            f"{e}\n\n{_diet_duration_prompt_message()}",
            reply_markup=_diet_duration_choice_markup(patient.id),
        )
        return
    await _send_wizard_inline_prompt(
        db,
        doctor,
        chat_id,
        channel_user_key,
        text=_diet_meals_prompt_message(),
        reply_markup=_diet_meals_choice_markup(patient.id),
        state_patch={
            "awaiting": "diet_meals_per_day",
            "strategy_flow": "new",
            "patient_id": patient.id,
            "instruction": instruction if isinstance(instruction, str) else None,
            "duration_days": ddays,
            "wizard_back_step": "diet_duration",
        },
    )


async def _transition_regen_duration_to_strategy(
    db: AsyncSession,
    doctor: Doctor,
    chat_id: str,
    channel_user_key: str,
    patient: Patient,
    diet_id: int,
    regen_instruction: str,
    ddays: int,
) -> None:
    try:
        ddays = validate_duration_days(ddays)
    except ValueError as e:
        await send_telegram_message(
            chat_id,
            f"{e}\n\n{_diet_duration_prompt_message()}",
            reply_markup=_diet_regen_duration_choice_markup(diet_id),
        )
        return
    await _send_wizard_inline_prompt(
        db,
        doctor,
        chat_id,
        channel_user_key,
        text=_diet_meals_prompt_message(),
        reply_markup=_diet_meals_choice_markup(patient.id),
        state_patch={
            "awaiting": "diet_meals_per_day",
            "strategy_flow": "regen",
            "patient_id": patient.id,
            "pending_diet_id": diet_id,
            "regen_instruction": regen_instruction,
            "duration_days": ddays,
            "wizard_back_step": "diet_regenerate_duration",
        },
    )


async def _persist_diet_confirm_and_show(
    db: AsyncSession,
    doctor: Doctor,
    chat_id: str,
    channel_user_key: str,
    wizard_state: dict[str, Any],
) -> None:
    patient_id = wizard_state.get("patient_id")
    if not isinstance(patient_id, int):
        return
    patient = await get_doctor_patient(db, doctor.id, patient_id)
    if not patient:
        await send_telegram_message(chat_id, "Paciente no encontrado.")
        return
    d_raw = wizard_state.get("duration_days")
    ddays = d_raw if isinstance(d_raw, int) else DEFAULT_PLAN_DURATION_DAYS
    flow = wizard_state.get("strategy_flow", "new")
    is_regen = flow == "regen"
    if is_regen:
        instr_raw = wizard_state.get("regen_instruction")
        instruction = instr_raw if isinstance(instr_raw, str) else ""
    else:
        instruction = wizard_state.get("instruction")
    instr_summary = (
        instruction.strip()
        if isinstance(instruction, str) and instruction.strip()
        else "(sin instrucción adicional)"
    )
    summary_strat = strategy_summary_lines(wizard_state)
    sm = wizard_state.get("strategy_mode")
    if sm not in ("auto", "guided", "manual"):
        sm = "auto"
    confirm_payload: dict[str, Any] = {
        "awaiting": "diet_confirm",
        "patient_id": patient.id,
        "duration_days": ddays,
        "meals_per_day": wizard_state.get("meals_per_day", 4),
        "strategy_mode": sm,
        "strategy_flow": flow,
        "wizard_back_step": _wizard_back_step_for_confirm(wizard_state),
    }
    if is_regen:
        pid = wizard_state.get("pending_diet_id")
        if isinstance(pid, int):
            confirm_payload["pending_diet_id"] = pid
        confirm_payload["regen_instruction"] = (
            instruction if isinstance(instruction, str) else ""
        )
        confirm_payload["instruction"] = (
            instruction if isinstance(instruction, str) else None
        )
    else:
        confirm_payload["instruction"] = (
            instruction if isinstance(instruction, str) else None
        )
    for k in (
        "diet_style",
        "macro_protein",
        "macro_carbs",
        "macro_fat",
        "manual_kcal",
        "manual_protein_g",
        "manual_carbs_g",
        "manual_fat_g",
    ):
        if k in wizard_state and wizard_state[k] is not None:
            confirm_payload[k] = wizard_state[k]
    await _save_state(db, doctor.id, channel_user_key, confirm_payload)
    await _send_diet_confirm_prompt(
        db,
        doctor,
        chat_id,
        channel_user_key,
        patient,
        body=_diet_confirm_body(
            patient,
            instruction_summary=instr_summary,
            duration_days=ddays,
            strategy_summary_lines=summary_strat,
            is_regenerate=is_regen,
        ),
    )


def _macro_btn_to_level(ch: str) -> Any:
    if ch == "s":
        return None
    return {"l": "low", "n": "normal", "h": "high"}.get(ch)


def _wizard_inline_matches(state: dict[str, Any], message: dict[str, Any]) -> bool:
    return _state_message_matches(
        state,
        key="wizard_inline_message_id",
        message=message,
    )


def _wizard_back_step_for_confirm(state: dict[str, Any]) -> str:
    sm = state.get("strategy_mode")
    if sm == "guided":
        return "diet_macro_fat"
    if sm == "auto":
        return "diet_strategy_mode"
    return "diet_manual_fat_g"


async def _handle_diet_meals_callback(
    db: AsyncSession,
    doctor: Doctor,
    chat_id: str,
    channel_user_key: str,
    *,
    patient_id_cb: int,
    meals_per_day: int,
    message: Optional[dict[str, Any]] = None,
) -> None:
    state = await _load_state_for_update(db, doctor.id, channel_user_key)
    if (
        state.get("awaiting") != "diet_meals_per_day"
        or state.get("patient_id") != patient_id_cb
        or (message is not None and not _wizard_inline_matches(state, message))
    ):
        await _send_stale_step_refresh(
            db,
            doctor,
            chat_id,
            channel_user_key,
            prefix="Este paso ya no aplica.",
        )
        return
    st = dict(state)
    st["meals_per_day"] = meals_per_day
    st["awaiting"] = "diet_strategy_mode"
    st["wizard_back_step"] = "diet_duration"
    await _send_wizard_inline_prompt(
        db,
        doctor,
        chat_id,
        channel_user_key,
        text=_diet_strategy_mode_prompt_message(),
        reply_markup=_diet_strategy_mode_markup(patient_id_cb),
        state_patch=st,
    )


async def _handle_diet_smd_callback(
    db: AsyncSession,
    doctor: Doctor,
    chat_id: str,
    channel_user_key: str,
    *,
    patient_id_cb: int,
    letter: str,
    message: Optional[dict[str, Any]] = None,
) -> None:
    state = await _load_state_for_update(db, doctor.id, channel_user_key)
    if (
        state.get("awaiting") != "diet_strategy_mode"
        or state.get("patient_id") != patient_id_cb
        or (message is not None and not _wizard_inline_matches(state, message))
    ):
        await _send_stale_step_refresh(
            db,
            doctor,
            chat_id,
            channel_user_key,
            prefix="Este paso ya no aplica.",
        )
        return
    patient = await get_doctor_patient(db, doctor.id, patient_id_cb)
    if not patient:
        await send_telegram_message(chat_id, "Paciente no encontrado.")
        return
    st = dict(state)
    if letter == "a":
        st["strategy_mode"] = "auto"
        _clear_guided_manual_fields(st)
        await _persist_diet_confirm_and_show(
            db, doctor, chat_id, channel_user_key, st
        )
    elif letter == "g":
        st["strategy_mode"] = "guided"
        for k in (
            "manual_kcal",
            "manual_protein_g",
            "manual_carbs_g",
            "manual_fat_g",
        ):
            st.pop(k, None)
        st.pop("diet_style", None)
        for k in ("macro_protein", "macro_carbs", "macro_fat"):
            st.pop(k, None)
        st["awaiting"] = "diet_strategy_style"
        st["wizard_back_step"] = "diet_meals_per_day"
        await _send_wizard_inline_prompt(
            db,
            doctor,
            chat_id,
            channel_user_key,
            text=_diet_strategy_style_prompt_message(),
            reply_markup=_diet_strategy_style_markup(patient_id_cb),
            state_patch=st,
        )
    elif letter == "m":
        st["strategy_mode"] = "manual"
        for k in ("diet_style", "macro_protein", "macro_carbs", "macro_fat"):
            st.pop(k, None)
        for k in (
            "manual_kcal",
            "manual_protein_g",
            "manual_carbs_g",
            "manual_fat_g",
        ):
            st.pop(k, None)
        st["awaiting"] = "diet_manual_kcal"
        st["wizard_back_step"] = "diet_strategy_mode"
        await _save_state(db, doctor.id, channel_user_key, st)
        await send_telegram_message(
            chat_id,
            _diet_manual_kcal_prompt_message(),
            reply_markup=_cancel_markup(),
        )
    else:
        await send_telegram_message(chat_id, "Opción no reconocida.")


async def _handle_diet_sty_callback(
    db: AsyncSession,
    doctor: Doctor,
    chat_id: str,
    channel_user_key: str,
    *,
    code: str,
    patient_id_cb: int,
    message: Optional[dict[str, Any]] = None,
) -> None:
    state = await _load_state_for_update(db, doctor.id, channel_user_key)
    if (
        state.get("awaiting") != "diet_strategy_style"
        or state.get("patient_id") != patient_id_cb
        or (message is not None and not _wizard_inline_matches(state, message))
    ):
        await _send_stale_step_refresh(
            db,
            doctor,
            chat_id,
            channel_user_key,
            prefix="Este paso ya no aplica.",
        )
        return
    if code not in STYLE_CODE_TO_API:
        await send_telegram_message(chat_id, "Estilo no reconocido.")
        return
    st = dict(state)
    api_style = STYLE_CODE_TO_API[code]
    if api_style:
        st["diet_style"] = api_style
    else:
        st.pop("diet_style", None)
    st["awaiting"] = "diet_macro_protein"
    st["wizard_back_step"] = "diet_strategy_mode"
    await _send_wizard_inline_prompt(
        db,
        doctor,
        chat_id,
        channel_user_key,
        text=_diet_macro_protein_prompt_message(),
        reply_markup=_diet_macro_protein_markup(),
        state_patch=st,
    )


async def _handle_diet_macro_callback(
    db: AsyncSession,
    doctor: Doctor,
    chat_id: str,
    channel_user_key: str,
    *,
    which: str,
    letter: str,
    message: Optional[dict[str, Any]] = None,
) -> None:
    awaiting_map = {
        "mp": "diet_macro_protein",
        "mc": "diet_macro_carbs",
        "mf": "diet_macro_fat",
    }
    next_await = {
        "mp": "diet_macro_carbs",
        "mc": "diet_macro_fat",
        "mf": None,
    }
    field = {"mp": "macro_protein", "mc": "macro_carbs", "mf": "macro_fat"}[
        which
    ]
    need = awaiting_map[which]
    state = await _load_state_for_update(db, doctor.id, channel_user_key)
    if state.get("awaiting") != need or (
        message is not None and not _wizard_inline_matches(state, message)
    ):
        await _send_stale_step_refresh(
            db,
            doctor,
            chat_id,
            channel_user_key,
            prefix="Este paso ya no aplica.",
        )
        return
    lvl = _macro_btn_to_level(letter)
    st = dict(state)
    if lvl is None:
        st.pop(field, None)
    else:
        st[field] = lvl
    nxt = next_await[which]
    if nxt is None:
        await _persist_diet_confirm_and_show(
            db, doctor, chat_id, channel_user_key, st
        )
        return
    st["awaiting"] = nxt
    st["wizard_back_step"] = "diet_macro_protein" if which == "mp" else "diet_macro_carbs"
    if which == "mp":
        await _send_wizard_inline_prompt(
            db,
            doctor,
            chat_id,
            channel_user_key,
            text=_diet_macro_carbs_prompt_message(),
            reply_markup=_diet_macro_carbs_markup(),
            state_patch=st,
        )
    else:
        await _send_wizard_inline_prompt(
            db,
            doctor,
            chat_id,
            channel_user_key,
            text=_diet_macro_fat_prompt_message(),
            reply_markup=_diet_macro_fat_markup(),
            state_patch=st,
        )


async def _execute_diet_confirm_from_snapshot(
    db: AsyncSession,
    doctor: Doctor,
    chat_id: str,
    channel_user_key: str,
    patient: Patient,
    snap: dict[str, Any],
) -> None:
    flow = snap.get("strategy_flow", "new")
    d_raw = snap.get("duration_days")
    duration_days = (
        d_raw if isinstance(d_raw, int) else DEFAULT_PLAN_DURATION_DAYS
    )
    strategy_slice = dict(snap)
    if flow == "regen":
        diet_id = snap.get("pending_diet_id")
        if not isinstance(diet_id, int):
            await send_telegram_message(
                chat_id,
                "No pude completar la regeneración (falta borrador).",
                reply_markup=_menu_markup(),
            )
            return
        regen_raw = snap.get("regen_instruction")
        regen_inst = regen_raw if isinstance(regen_raw, str) else ""
        await _complete_diet_regenerate_with_duration(
            db,
            doctor,
            chat_id,
            channel_user_key,
            patient,
            diet_id,
            regen_inst,
            duration_days,
            strategy_state=strategy_slice,
        )
        return
    instr = snap.get("instruction")
    clean = (
        instr.strip() if isinstance(instr, str) and instr.strip() else None
    )
    await _execute_diet_generation(
        db,
        doctor,
        chat_id,
        channel_user_key,
        patient,
        clean,
        duration_days=duration_days,
        strategy_state=strategy_slice,
    )


async def _complete_diet_regenerate_with_duration(
    db: AsyncSession,
    doctor: Doctor,
    chat_id: str,
    channel_user_key: str,
    patient: Patient,
    diet_id: int,
    regen_instruction: str,
    ddays: int,
    *,
    strategy_state: Optional[dict[str, Any]] = None,
) -> None:
    diet_row = await get_doctor_diet(db, doctor.id, diet_id)
    if not diet_row or diet_row.status != "pending_approval":
        await _clear_state(db, doctor.id, channel_user_key)
        await send_telegram_message(
            chat_id,
            "Ese borrador ya no está disponible para regenerar.",
            reply_markup=_menu_markup(),
        )
        return
    try:
        ddays = validate_duration_days(ddays)
    except ValueError as e:
        await send_telegram_message(
            chat_id,
            f"{e}\n\n{_diet_duration_prompt_message()}",
            reply_markup=_diet_regen_duration_choice_markup(diet_id),
        )
        return
    skw = diet_strategy_kwargs_from_state(strategy_state or {})
    try:
        diet = await regenerate_diet(
            db,
            doctor,
            diet_id,
            regen_instruction if regen_instruction.strip() else None,
            diet_status="pending_approval",
            duration_days=ddays,
            **skw,
        )
    except DietGenerationError as e:
        msg = "\n".join(e.reasons) if e.reasons else e.message
        await send_telegram_message(chat_id, msg[:4090])
        return
    await _send_diet_preview_and_store_state(
        db,
        doctor,
        chat_id,
        channel_user_key,
        diet,
        patient,
        doctor_note=diet.notes,
    )


def _metric_confirm_markup(patient_id: int, kind: str) -> dict:
    return {
        "inline_keyboard": [
            [
                {
                    "text": "Confirmar",
                    "callback_data": f"metric:confirm:{patient_id}:{kind}",
                },
                {
                    "text": "Cancelar",
                    "callback_data": f"metric:cancel:{patient_id}",
                },
            ]
        ]
    }


def _is_weight_request(text: str) -> bool:
    t = text.lower()
    return any(
        token in t
        for token in (
            "peso",
            "kg",
            "lb",
            "libras",
            "actualiza peso",
            "agregar peso",
            "poner peso",
        )
    )


def _is_height_request(text: str) -> bool:
    t = text.lower()
    return any(
        token in t
        for token in (
            "estatura",
            "altura",
            "talla",
            "cm",
            "metros",
            "metro",
            "pies",
            "pulg",
            "actualiza estatura",
            "agregar estatura",
            "poner altura",
            "falta estatura",
        )
    )


def _is_height_blocker(reasons: list[str]) -> bool:
    return any("height" in reason.lower() for reason in reasons)


async def _classify_user_intent(text: str) -> tuple[str, str, dict[str, Any]]:
    intent, rule_policy, entities = rule_based_intent(text)
    if intent != "unknown":
        return intent, INTENT_POLICY.get(intent, rule_policy), entities
    if settings.OPENAI_API_KEY:
        llm = await classify_intent_llm(text)
        if llm and float(llm.get("confidence") or 0) >= 0.5:
            li = str(llm.get("intent") or "unknown")
            if li in INTENT_POLICY and li != "unknown":
                out_e = dict(entities)
                pn = llm.get("patient_name")
                if pn:
                    out_e["patient_name"] = str(pn).strip()
                return li, INTENT_POLICY[li], out_e
    if rule_policy == "ambiguous_entity":
        return intent, "ambiguous_entity", entities
    return "unknown", "unmapped", entities


def _patient_name_hint(text: str, entities: dict[str, Any]) -> str:
    pn = entities.get("patient_name")
    if pn:
        return str(pn).strip()
    return _extract_diet_patient_hint(text)


async def _maybe_send_first_welcome(
    db: AsyncSession,
    doctor: Doctor,
    chat_id: str,
    channel_user_key: str,
) -> None:
    state = await _load_state(db, doctor.id, channel_user_key)
    if state.get("welcome_shown"):
        return
    await _send_home_screen(db, doctor, chat_id, channel_user_key)
    await _save_state(
        db, doctor.id, channel_user_key, {"welcome_shown": True}
    )


async def _send_patient_history_ui(
    db: AsyncSession,
    doctor: Doctor,
    chat_id: str,
    patient_id: int,
    channel_user_key: str,
    *,
    page: int = 1,
    prefix: str | None = None,
    back_state: Optional[dict[str, Any]] = None,
) -> None:
    diets, total = await list_patient_diets(
        db, doctor.id, patient_id, page=page, page_size=5
    )
    if not diets:
        await send_telegram_message(chat_id, "Este paciente no tiene dietas aún.")
        return
    lines = ["Historial de dietas:"]
    actions: list[list[dict]] = []
    for d in diets:
        lines.append(f"• #{d.id} · {d.created_at.date()}")
        actions.append(
            [
                {
                    "text": f"PDF Dieta #{d.id}",
                    "callback_data": f"diet:pdf:{d.id}",
                }
            ]
        )
    lines.append(f"Página {page} · Total: {total}")
    pagination = _history_pagination_markup(patient_id, page, total, 5)
    text = "\n".join(lines)
    if prefix:
        text = f"{prefix}\n\n{text}"
    await _send_navigation_message(
        db,
        doctor,
        chat_id,
        channel_user_key,
        screen="patient_history",
        text=text,
        reply_markup={"inline_keyboard": actions + pagination["inline_keyboard"]},
        state_patch={
            "navigation_patient_id": patient_id,
            "navigation_page": page,
            "navigation_query": None,
        },
        back_state=back_state
        if back_state is not None
        else _navigation_back_state("patient_card", patient_id=patient_id),
    )


async def _queue_metric_confirmation(
    db: AsyncSession,
    doctor: Doctor,
    chat_id: str,
    channel_user_key: str,
    patient: Patient,
    *,
    weight_kg: float | None = None,
    height_cm: float | None = None,
    resume_after: str | None = None,
    resume_instruction: str | None = None,
    resume_duration_days: int | None = None,
    resume_diet_context: Optional[dict[str, Any]] = None,
) -> None:
    if weight_kg is not None:
        payload_w: dict[str, Any] = {
            "awaiting": "metric_confirm",
            "patient_id": patient.id,
            "pending_weight_kg": weight_kg,
            "pending_height_cm": None,
            "resume_after": resume_after,
            "instruction": resume_instruction,
            "duration_days": resume_duration_days
            if resume_duration_days is not None
            else DEFAULT_PLAN_DURATION_DAYS,
        }
        if resume_diet_context:
            payload_w.update(_diet_wizard_persist_slice(resume_diet_context))
            if resume_instruction is not None:
                payload_w["instruction"] = resume_instruction
        await _save_state(
            db,
            doctor.id,
            channel_user_key,
            payload_w,
        )
        mid = await send_telegram_message(
            chat_id,
            f"¿Confirmar peso {weight_kg:.2f} kg para {patient.first_name} {patient.last_name}?",
            reply_markup=_metric_confirm_markup(patient.id, "weight"),
        )
        await _save_state(
            db,
            doctor.id,
            channel_user_key,
            {"metric_confirm_message_id": mid},
        )
        return
    if height_cm is not None:
        payload_h: dict[str, Any] = {
            "awaiting": "metric_confirm",
            "patient_id": patient.id,
            "pending_height_cm": height_cm,
            "pending_weight_kg": None,
            "resume_after": resume_after,
            "instruction": resume_instruction,
            "duration_days": resume_duration_days
            if resume_duration_days is not None
            else DEFAULT_PLAN_DURATION_DAYS,
        }
        if resume_diet_context:
            payload_h.update(_diet_wizard_persist_slice(resume_diet_context))
            if resume_instruction is not None:
                payload_h["instruction"] = resume_instruction
        await _save_state(
            db,
            doctor.id,
            channel_user_key,
            payload_h,
        )
        mid = await send_telegram_message(
            chat_id,
            f"¿Confirmar estatura {height_cm:.1f} cm para {patient.first_name} {patient.last_name}?",
            reply_markup=_metric_confirm_markup(patient.id, "height"),
        )
        await _save_state(
            db,
            doctor.id,
            channel_user_key,
            {"metric_confirm_message_id": mid},
        )
        return


def _patient_actions_markup(patient_id: int) -> dict:
    return {
        "inline_keyboard": [
            [
                {"text": "Generar dieta", "callback_data": f"patient:diet:{patient_id}"},
                {"text": "Historial dietas", "callback_data": f"patient:history:{patient_id}:1"},
            ],
            *_navigation_footer_markup(include_back=True),
        ]
    }


def _history_pagination_markup(patient_id: int, page: int, total: int, page_size: int) -> dict:
    total_pages = max(1, (total + page_size - 1) // page_size)
    row: list[dict] = []
    if page > 1:
        row.append(
            {
                "text": "⬅️",
                "callback_data": f"patient:history:{patient_id}:{page - 1}",
            }
        )
    row.append({"text": f"{page}/{total_pages}", "callback_data": "noop"})
    if page < total_pages:
        row.append(
            {
                "text": "➡️",
                "callback_data": f"patient:history:{patient_id}:{page + 1}",
            }
        )
    keyboard = [row] if row else []
    keyboard.extend(_navigation_footer_markup(include_back=True))
    return {"inline_keyboard": keyboard}


async def _execute_diet_generation(
    db: AsyncSession,
    doctor: Doctor,
    chat_id: str,
    channel_user_key: str,
    patient: Patient,
    instruction: Optional[str],
    *,
    duration_days: int = DEFAULT_PLAN_DURATION_DAYS,
    strategy_state: Optional[dict[str, Any]] = None,
) -> None:
    skw = diet_strategy_kwargs_from_state(strategy_state or {})
    try:
        diet = await create_new_diet(
            db,
            doctor,
            patient.id,
            instruction,
            diet_status="pending_approval",
            duration_days=duration_days,
            **skw,
        )
    except DietGenerationError as e:
        if _is_height_blocker(e.reasons):
            height_resume: dict[str, Any] = {
                "awaiting": "height_cm",
                "patient_id": patient.id,
                "resume_after": "diet_confirm",
                "instruction": instruction,
                "duration_days": duration_days,
                "last_active_patient_id": patient.id,
            }
            if strategy_state:
                height_resume.update(_diet_wizard_persist_slice(strategy_state))
            await _save_state(
                db,
                doctor.id,
                channel_user_key,
                height_resume,
            )
            await send_telegram_message(
                chat_id,
                "Para generar la dieta necesito la estatura actual en el sistema. "
                "Envíamela aquí en cm, m o pies/pulgadas.",
                reply_markup=_cancel_markup(),
            )
            return
        msg = "\n".join(e.reasons) if e.reasons else e.message
        await send_telegram_message(chat_id, msg[:4090])
        return
    await _send_diet_preview_and_store_state(
        db,
        doctor,
        chat_id,
        channel_user_key,
        diet,
        patient,
        doctor_note=instruction,
    )


async def _start_guided_diet_flow(
    db: AsyncSession,
    doctor: Doctor,
    chat_id: str,
    channel_user_key: str,
    patient: Patient,
) -> None:
    await _remember_patient_context(db, doctor.id, channel_user_key, patient.id)
    profile = await get_patient_profile(db, patient.id)
    metric = await latest_metric(db, patient.id)
    await send_telegram_message(
        chat_id,
        format_patient_summary(patient, profile=profile, metric=metric),
    )
    await _save_state(
        db,
        doctor.id,
        channel_user_key,
        {
            "awaiting": "diet_note_offer",
            "patient_id": patient.id,
            "navigation_message_id": None,
        },
    )
    await _send_wizard_inline_prompt(
        db,
        doctor,
        chat_id,
        channel_user_key,
        text=(
            "¿Quieres agregar una nota o especificaciones extra para orientar la generación "
            "de la dieta? Es opcional."
        ),
        reply_markup=_diet_note_offer_markup(patient.id),
    )


async def _show_patient_card(
    db: AsyncSession,
    doctor: Doctor,
    chat_id: str,
    channel_user_key: str,
    patient: Patient,
    *,
    prefix: str | None = None,
    back_state: Optional[dict[str, Any]] = None,
) -> None:
    await _remember_patient_context(db, doctor.id, channel_user_key, patient.id)
    profile = await get_patient_profile(db, patient.id)
    metric = await latest_metric(db, patient.id)
    text = format_patient_summary(patient, profile=profile, metric=metric)
    if prefix:
        text = f"{prefix}\n\n{text}"
    await _send_navigation_message(
        db,
        doctor,
        chat_id,
        channel_user_key,
        screen="patient_card",
        text=text,
        reply_markup=_patient_actions_markup(patient.id),
        state_patch={
            "navigation_patient_id": patient.id,
            "navigation_page": None,
            "navigation_query": None,
        },
        back_state=back_state
        if back_state is not None
        else _navigation_back_state("patients", page=1),
    )


async def _send_ambiguous_patient_buttons(
    db: AsyncSession,
    doctor: Doctor,
    chat_id: str,
    channel_user_key: str,
    rows: list[Patient],
    *,
    header: str = "Varios pacientes coinciden. Elige uno:",
    prefix: str | None = None,
    back_state: Optional[dict[str, Any]] = None,
) -> None:
    lines = [header]
    patient_rows: list[list[dict]] = []
    for p in rows:
        lines.append(f"• {patient_identity_label(p)}")
        patient_rows.append(
            [
                {
                    "text": f"{p.first_name} {p.last_name} #{p.id}",
                    "callback_data": f"patient:select:{p.id}",
                }
            ]
        )
    text = "\n".join(lines)
    if prefix:
        text = f"{prefix}\n\n{text}"
    include_back = bool(
        back_state
        and isinstance(back_state.get("navigation_back_screen"), str)
        and back_state.get("navigation_back_screen")
    )
    await _send_navigation_message(
        db,
        doctor,
        chat_id,
        channel_user_key,
        screen="patient_picker",
        text=text,
        reply_markup={
            "inline_keyboard": patient_rows
            + _navigation_footer_markup(include_back=include_back)
        },
        state_patch={
            "navigation_patient_id": None,
            "navigation_page": None,
            "navigation_query": None,
            "navigation_picker_patient_ids": [p.id for p in rows],
            "navigation_picker_header": header,
        },
        back_state=back_state if back_state is not None else _navigation_back_state("home"),
    )


def _patients_pagination_markup(
    page: int, total: int, query: str | None
) -> dict[str, list[list[dict]]]:
    total_pages = max(1, (total + PATIENTS_PAGE_SIZE - 1) // PATIENTS_PAGE_SIZE)
    row: list[dict] = []
    query_part = query or "_"
    if page > 1:
        row.append(
            {
                "text": "⬅️",
                "callback_data": f"menu:patients:{page - 1}:{query_part}",
            }
        )
    row.append({"text": f"{page}/{total_pages}", "callback_data": "noop"})
    if page < total_pages:
        row.append(
            {
                "text": "➡️",
                "callback_data": f"menu:patients:{page + 1}:{query_part}",
            }
        )
    keyboard = [row] if row else []
    search_row = [{"text": "Buscar", "callback_data": "menu:search"}]
    if query:
        search_row.append({"text": "Limpiar", "callback_data": "menu:patients:1"})
    keyboard.append(search_row)
    keyboard.extend(_navigation_footer_markup(include_back=False))
    return {"inline_keyboard": keyboard}


async def _send_patients_page(
    db: AsyncSession,
    doctor: Doctor,
    chat_id: str,
    channel_user_key: str,
    *,
    page: int = 1,
    query: str | None = None,
    prefix: str | None = None,
) -> None:
    items, total = await search_doctor_patients(
        db,
        doctor.id,
        query=query,
        page=page,
        page_size=PATIENTS_PAGE_SIZE,
    )
    if not items:
        await send_telegram_message(chat_id, "No encontré pacientes con ese criterio.")
        return
    lines = ["Selecciona un paciente:"]
    patient_rows: list[list[dict]] = []
    for patient in items:
        lines.append(f"• {patient_identity_label(patient)}")
        patient_rows.append(
            [
                {
                    "text": f"{patient.first_name} {patient.last_name} #{patient.id}",
                    "callback_data": f"patient:select:{patient.id}",
                }
            ]
        )
    footer_markup = _patients_pagination_markup(page, total, query)
    text = "\n".join(lines)
    if prefix:
        text = f"{prefix}\n\n{text}"
    await _send_navigation_message(
        db,
        doctor,
        chat_id,
        channel_user_key,
        screen="patients",
        text=text,
        reply_markup={
            "inline_keyboard": patient_rows + footer_markup["inline_keyboard"]
        },
        state_patch={
            "navigation_patient_id": None,
            "navigation_page": page,
            "navigation_query": query,
        },
        back_state=_navigation_back_state("home"),
    )


def _apply_tg_meal_text_to_plan(
    plan: dict[str, Any], day_0: int, slot: str, meal_text: str
) -> None:
    days = plan.get("days")
    if not isinstance(days, list) or day_0 < 0 or day_0 >= len(days):
        return
    day = days[day_0]
    if not isinstance(day, dict):
        return
    t = meal_text.strip()
    meals = day.get("meals")
    if not isinstance(meals, dict):
        meals = {}
    meals[slot] = t
    day["meals"] = meals
    day[slot] = t


async def _send_telegram_diet_fulldays(
    chat_id: str, plan: dict[str, Any], num_days: int
) -> None:
    await send_telegram_message(
        chat_id,
        f"Detalle de comidas por día (ciclo base) — {num_days} día(s).",
    )
    for d0 in range(num_days):
        block = format_telegram_full_day_block(plan, d0, num_days=num_days)
        for chunk in split_telegram_text_chunks(block, 4000):
            await send_telegram_message(chat_id, chunk)


async def _handle_diet_tg_edit_meal_text(
    db: AsyncSession,
    doctor: Doctor,
    chat_id: str,
    channel_user_key: str,
    text: str,
    state: dict,
    normalized: str,
) -> bool:
    diet_id = state.get("pending_diet_id")
    day_1 = state.get("edit_meal_day")
    slot_i = state.get("edit_meal_slot_index")
    if (
        not isinstance(diet_id, int)
        or not isinstance(day_1, int)
        or not isinstance(slot_i, int)
    ):
        await _send_stale_step_refresh(
            db,
            doctor,
            chat_id,
            channel_user_key,
            prefix="Este paso ya no aplica.",
        )
        return True
    if normalized in {
        "cancelar",
        "cancel",
        "salir",
        "saltar",
        "atrás",
        "atras",
        "volver",
    }:
        pat_id = state.get("patient_id")
        mid = await send_telegram_message(
            chat_id,
            "Cambio descartado. Sigue con la vista previa.",
            reply_markup=_diet_preview_markup(diet_id),
        )
        st: dict[str, Any] = {
            "awaiting": "diet_preview",
            "pending_diet_id": diet_id,
            "preview_message_id": mid,
            "edit_day_message_id": None,
            "edit_slot_message_id": None,
        }
        if isinstance(pat_id, int):
            st["patient_id"] = pat_id
        await _save_state(db, doctor.id, channel_user_key, st)
        return True
    diet = await db.get(Diet, diet_id)
    if diet is None or diet.doctor_id != doctor.id:
        await send_telegram_message(chat_id, "Dieta no encontrada.")
        return True
    if diet.status != "pending_approval":
        await _clear_state(db, doctor.id, channel_user_key)
        await send_telegram_message(
            chat_id,
            "Este borrador ya no está pendiente de aprobación.",
            reply_markup=_menu_markup(),
        )
        return True
    day_0 = day_1 - 1
    raw = diet.structured_plan_json
    if not isinstance(raw, dict):
        await send_telegram_message(
            chat_id, "No hay estructura de plan para editar."
        )
        return True
    plan = copy.deepcopy(raw)
    slots = resolve_plan_meal_slots(plan)
    if slot_i < 0 or slot_i >= len(slots):
        await send_telegram_message(
            chat_id, "Ese intervalo de comida ya no existe. Elige otra comida."
        )
        return True
    if len(text) > _DIET_TG_MEAL_TEXT_MAX:
        await send_telegram_message(
            chat_id,
            f"Texto demasiado largo (máx. {_DIET_TG_MEAL_TEXT_MAX} caracteres). Reenvía un texto más corto.",
            reply_markup=_cancel_markup(),
        )
        return True
    if not text.strip():
        await send_telegram_message(
            chat_id,
            "Escribe el contenido de la comida o escribe «cancelar» para volver a la vista previa.",
        )
        return True
    slot_key = slots[slot_i]
    days_list = plan.get("days")
    old_day = (
        days_list[day_0]
        if isinstance(days_list, list) and 0 <= day_0 < len(days_list)
        else {}
    )
    old_meals = old_day.get("meals") if isinstance(old_day, dict) else {}
    old_value = (
        old_meals.get(slot_key)
        if isinstance(old_meals, dict)
        else old_day.get(slot_key) if isinstance(old_day, dict) else None
    )
    old_text = old_value.strip() if isinstance(old_value, str) else ""
    new_text = text.strip()
    _apply_tg_meal_text_to_plan(plan, day_0, slot_key, text)
    new_plan = normalize_plan_meal_metadata(plan)
    diet.structured_plan_json = new_plan
    diet.updated_at = utcnow()
    db.add(
        AuditLog(
            doctor_id=doctor.id,
            action="diet_edit_meal_manual",
            entity_type="diet",
            entity_id=diet.id,
            payload_json={
                "patient_id": diet.patient_id,
                "day": day_1,
                "slot": slot_key,
                "old_text_length": len(old_text),
                "new_text_length": len(new_text),
                "channel": "telegram",
            },
        )
    )
    await db.flush()
    patient = await get_doctor_patient(db, doctor.id, diet.patient_id)
    if not patient:
        await _clear_state(db, doctor.id, channel_user_key)
        await send_telegram_message(chat_id, "Paciente no encontrado.")
        return True
    await _save_state(
        db,
        doctor.id,
        channel_user_key,
        {
            "awaiting": "diet_preview",
            "pending_diet_id": diet.id,
            "patient_id": patient.id,
            "edit_day_message_id": None,
            "edit_slot_message_id": None,
        },
    )
    await send_telegram_message(chat_id, "Comida actualizada. Vista previa:")
    preview = _format_diet_preview_message(diet, patient, doctor_note=diet.notes)
    mid = await send_telegram_message(
        chat_id, preview, reply_markup=_diet_preview_markup(diet.id)
    )
    await _save_state(
        db,
        doctor.id,
        channel_user_key,
        {"preview_message_id": mid},
    )
    return True


async def _handle_stateful_text(
    db: AsyncSession,
    doctor: Doctor,
    chat_id: str,
    channel_user_key: str,
    text: str,
) -> bool:
    state = await _load_state(db, doctor.id, channel_user_key)
    awaiting = state.get("awaiting")
    if not awaiting:
        return False
    normalized = text.strip().lower()

    if awaiting == "diet_tg_edit_meal":
        return await _handle_diet_tg_edit_meal_text(
            db, doctor, chat_id, channel_user_key, text, state, normalized
        )

    if awaiting == "diet_note_offer":
        patient_id = state.get("patient_id")
        if not isinstance(patient_id, int):
            await _clear_state(db, doctor.id, channel_user_key)
            return False
        patient = await get_doctor_patient(db, doctor.id, patient_id)
        if not patient:
            await send_telegram_message(chat_id, "Paciente no encontrado.")
            await _clear_state(db, doctor.id, channel_user_key)
            return True
        skip_note = normalized in {
            "no",
            "n",
            "sin nota",
            "saltar",
            "skip",
            "ninguna",
            "no gracias",
            "no, gracias",
            "no gracias.",
        }
        if skip_note:
            await _save_state(
                db,
                doctor.id,
                channel_user_key,
                {
                    "awaiting": "diet_duration",
                    "patient_id": patient.id,
                    "instruction": None,
                    "wizard_back_step": "diet_note_offer",
                },
            )
            await send_telegram_message(
                chat_id,
                _diet_duration_prompt_message(),
                reply_markup=_diet_duration_choice_markup(patient.id),
            )
            return True
        if normalized in {"si", "sí", "yes"}:
            await _save_state(
                db,
                doctor.id,
                channel_user_key,
                {"awaiting": "diet_instruction", "patient_id": patient.id},
            )
            await send_telegram_message(
                chat_id,
                "Escribe la nota o especificaciones extra para la IA (ej.: más proteína, sin mariscos). "
                "Si cambias de idea, escribe «saltar».",
                reply_markup=_cancel_markup(),
            )
            return True
        if text.strip():
            instruction = text.strip()
            await _save_state(
                db,
                doctor.id,
                channel_user_key,
                {
                    "awaiting": "diet_duration",
                    "patient_id": patient.id,
                    "instruction": instruction,
                    "wizard_back_step": "diet_note_offer",
                },
            )
            await send_telegram_message(
                chat_id,
                _diet_duration_prompt_message(),
                reply_markup=_diet_duration_choice_markup(patient.id),
            )
            return True
        await send_telegram_message(
            chat_id,
            "Indica si quieres nota con los botones, escribe «sí» o «no», "
            "o envía directamente el texto de la nota.",
            reply_markup=_diet_note_offer_markup(patient.id),
        )
        return True

    if awaiting == "diet_duration":
        patient_id = state.get("patient_id")
        if not isinstance(patient_id, int):
            await _clear_state(db, doctor.id, channel_user_key)
            return False
        patient = await get_doctor_patient(db, doctor.id, patient_id)
        if not patient:
            await send_telegram_message(chat_id, "Paciente no encontrado.")
            await _clear_state(db, doctor.id, channel_user_key)
            return True
        try:
            ddays = parse_duration_text(text)
        except DurationParseError as e:
            await send_telegram_message(
                chat_id,
                f"{e}\n\n{_diet_duration_prompt_message()}",
                reply_markup=_diet_duration_choice_markup(patient.id),
            )
            return True
        instruction = state.get("instruction")
        await _transition_new_diet_duration_to_strategy(
            db,
            doctor,
            chat_id,
            channel_user_key,
            patient,
            instruction if isinstance(instruction, str) else None,
            ddays,
        )
        return True

    if awaiting == "diet_strategy_mode":
        pid = state.get("patient_id")
        if isinstance(pid, int):
            await send_telegram_message(
                chat_id,
                "Elige una opción con los botones: Automático, Guiado o Manual.",
                reply_markup=_diet_strategy_mode_markup(pid),
            )
        return True

    if awaiting == "diet_meals_per_day":
        pid = state.get("patient_id")
        if normalized in {"2", "3", "4", "5"} and isinstance(pid, int):
            st = dict(state)
            st["meals_per_day"] = int(normalized)
            st["awaiting"] = "diet_strategy_mode"
            await _save_state(db, doctor.id, channel_user_key, st)
            await send_telegram_message(
                chat_id,
                _diet_strategy_mode_prompt_message(),
                reply_markup=_diet_strategy_mode_markup(pid),
            )
            return True
        if isinstance(pid, int):
            await send_telegram_message(
                chat_id,
                "Elige 2, 3, 4 o 5 comidas por día.",
                reply_markup=_diet_meals_choice_markup(pid),
            )
        return True

    if awaiting == "diet_strategy_style":
        pid = state.get("patient_id")
        if isinstance(pid, int):
            await send_telegram_message(
                chat_id,
                "Elige el estilo con los botones de abajo.",
                reply_markup=_diet_strategy_style_markup(pid),
            )
        return True

    if awaiting == "diet_macro_protein":
        await send_telegram_message(
            chat_id,
            "Usa los botones para la preferencia de proteína.",
            reply_markup=_diet_macro_protein_markup(),
        )
        return True

    if awaiting == "diet_macro_carbs":
        await send_telegram_message(
            chat_id,
            "Usa los botones para la preferencia de carbohidratos.",
            reply_markup=_diet_macro_carbs_markup(),
        )
        return True

    if awaiting == "diet_macro_fat":
        await send_telegram_message(
            chat_id,
            "Usa los botones para la preferencia de grasas.",
            reply_markup=_diet_macro_fat_markup(),
        )
        return True

    if awaiting == "diet_manual_kcal":
        st = dict(state)
        if normalized in {"saltar", "skip"}:
            st.pop("manual_kcal", None)
        else:
            try:
                v = float(text.replace(",", ".").strip())
                if v <= 0:
                    raise ValueError
                st["manual_kcal"] = int(round(v))
            except ValueError:
                await send_telegram_message(
                    chat_id,
                    "No reconocí un número válido. "
                    + _diet_manual_kcal_prompt_message(),
                    reply_markup=_cancel_markup(),
                )
                return True
        st["awaiting"] = "diet_manual_protein_g"
        await _save_state(db, doctor.id, channel_user_key, st)
        await send_telegram_message(
            chat_id,
            _diet_manual_protein_prompt_message(),
            reply_markup=_cancel_markup(),
        )
        return True

    if awaiting == "diet_manual_protein_g":
        st = dict(state)
        if normalized in {"saltar", "skip"}:
            st.pop("manual_protein_g", None)
        else:
            try:
                v = float(text.replace(",", ".").strip())
                if v <= 0:
                    raise ValueError
                st["manual_protein_g"] = v
            except ValueError:
                await send_telegram_message(
                    chat_id,
                    "No reconocí un número válido. "
                    + _diet_manual_protein_prompt_message(),
                    reply_markup=_cancel_markup(),
                )
                return True
        st["awaiting"] = "diet_manual_carbs_g"
        await _save_state(db, doctor.id, channel_user_key, st)
        await send_telegram_message(
            chat_id,
            _diet_manual_carbs_prompt_message(),
            reply_markup=_cancel_markup(),
        )
        return True

    if awaiting == "diet_manual_carbs_g":
        st = dict(state)
        if normalized in {"saltar", "skip"}:
            st.pop("manual_carbs_g", None)
        else:
            try:
                v = float(text.replace(",", ".").strip())
                if v <= 0:
                    raise ValueError
                st["manual_carbs_g"] = v
            except ValueError:
                await send_telegram_message(
                    chat_id,
                    "No reconocí un número válido. "
                    + _diet_manual_carbs_prompt_message(),
                    reply_markup=_cancel_markup(),
                )
                return True
        st["awaiting"] = "diet_manual_fat_g"
        await _save_state(db, doctor.id, channel_user_key, st)
        await send_telegram_message(
            chat_id,
            _diet_manual_fat_prompt_message(),
            reply_markup=_cancel_markup(),
        )
        return True

    if awaiting == "diet_manual_fat_g":
        st = dict(state)
        if normalized in {"saltar", "skip"}:
            st.pop("manual_fat_g", None)
        else:
            try:
                v = float(text.replace(",", ".").strip())
                if v <= 0:
                    raise ValueError
                st["manual_fat_g"] = v
            except ValueError:
                await send_telegram_message(
                    chat_id,
                    "No reconocí un número válido. "
                    + _diet_manual_fat_prompt_message(),
                    reply_markup=_cancel_markup(),
                )
                return True
        await _persist_diet_confirm_and_show(
            db, doctor, chat_id, channel_user_key, st
        )
        return True

    if awaiting == "diet_preview":
        pid = state.get("pending_diet_id")
        rm = (
            _diet_preview_markup(pid)
            if isinstance(pid, int)
            else None
        )
        await send_telegram_message(
            chat_id,
            "Para continuar usa los botones de la vista previa: "
            "«Aprobar y enviar PDF», «Regenerar con nueva nota» o «Descartar borrador».",
            reply_markup=rm,
        )
        return True

    if normalized in {"cancelar", "salir", "cancel", "no"}:
        await _clear_state(db, doctor.id, channel_user_key)
        await send_telegram_message(chat_id, "Flujo cancelado.", reply_markup=_menu_markup())
        return True
    if awaiting == "search_query":
        await _save_state(
            db,
            doctor.id,
            channel_user_key,
            {"awaiting": None, "last_search": text.strip()},
        )
        await _send_patients_page(
            db,
            doctor,
            chat_id,
            channel_user_key,
            page=1,
            query=text.strip(),
        )
        return True
    if awaiting == "metric_confirm":
        await send_telegram_message(
            chat_id,
            "Usa los botones «Confirmar» o «Cancelar» del mensaje anterior.",
        )
        return True
    patient_id = state.get("patient_id")
    if not isinstance(patient_id, int):
        await _clear_state(db, doctor.id, channel_user_key)
        return False
    patient = await get_doctor_patient(db, doctor.id, patient_id)
    if not patient:
        await send_telegram_message(chat_id, "Paciente no encontrado.")
        await _clear_state(db, doctor.id, channel_user_key)
        return True
    if awaiting == "weight_kg":
        instruction = state.get("instruction")
        resume_after = state.get("resume_after")
        rdur = state.get("duration_days")
        resume_dur = rdur if isinstance(rdur, int) else None
        value_kg: float | None = None
        parsed_w = parse_weight(text)
        if (
            parsed_w
            and parsed_w.field == "weight_kg"
            and measurement_in_reasonable_range(parsed_w)
        ):
            value_kg = parsed_w.normalized_value
        else:
            try:
                v = float(text.replace(",", ".").strip())
                if 20 <= v <= 400:
                    value_kg = v
            except ValueError:
                pass
        if value_kg is None:
            await send_telegram_message(
                chat_id,
                "No reconocí un peso válido. Ejemplos: 72,5 kg · 160 lb · 71,4 (solo número en este paso).",
            )
            return True
        rctx = (
            state
            if resume_after == "diet_confirm"
            else None
        )
        await _queue_metric_confirmation(
            db,
            doctor,
            chat_id,
            channel_user_key,
            patient,
            weight_kg=value_kg,
            resume_after=resume_after if isinstance(resume_after, str) else None,
            resume_instruction=instruction if isinstance(instruction, str) else None,
            resume_duration_days=resume_dur,
            resume_diet_context=rctx,
        )
        return True
    if awaiting == "height_cm":
        instruction = state.get("instruction")
        resume_after = state.get("resume_after")
        rdur = state.get("duration_days")
        resume_dur = rdur if isinstance(rdur, int) else None
        value_cm: float | None = None
        parsed_h = parse_height(text)
        if (
            parsed_h
            and parsed_h.field == "height_cm"
            and measurement_in_reasonable_range(parsed_h)
        ):
            value_cm = parsed_h.normalized_value
        else:
            try:
                v = float(text.replace(",", ".").strip())
                if 80 <= v <= 250:
                    value_cm = v
            except ValueError:
                pass
        if value_cm is None:
            await send_telegram_message(
                chat_id,
                "No reconocí una estatura válida. Ejemplos: 165 cm · 1,75 m · 5 pies 8 pulgadas.",
            )
            return True
        rctx_h = (
            state
            if resume_after == "diet_confirm"
            else None
        )
        await _queue_metric_confirmation(
            db,
            doctor,
            chat_id,
            channel_user_key,
            patient,
            height_cm=value_cm,
            resume_after=resume_after if isinstance(resume_after, str) else None,
            resume_instruction=instruction if isinstance(instruction, str) else None,
            resume_duration_days=resume_dur,
            resume_diet_context=rctx_h,
        )
        return True
    if awaiting == "diet_instruction":
        instruction: Optional[str]
        if normalized in {"saltar", "skip", "ninguna", "sin nota"}:
            instruction = None
        else:
            instruction = text.strip()
        await _save_state(
            db,
            doctor.id,
            channel_user_key,
            {
                "awaiting": "diet_duration",
                "patient_id": patient.id,
                "instruction": instruction,
                "wizard_back_step": "diet_instruction",
            },
        )
        await send_telegram_message(
            chat_id,
            _diet_duration_prompt_message(),
            reply_markup=_diet_duration_choice_markup(patient.id),
        )
        return True
    if awaiting == "diet_regenerate_note":
        diet_id = state.get("pending_diet_id")
        if not isinstance(diet_id, int):
            await _clear_state(db, doctor.id, channel_user_key)
            return False
        diet_row = await get_doctor_diet(db, doctor.id, diet_id)
        if not diet_row or diet_row.status != "pending_approval":
            await _clear_state(db, doctor.id, channel_user_key)
            await send_telegram_message(
                chat_id,
                "Ese borrador ya no está disponible para regenerar.",
                reply_markup=_menu_markup(),
            )
            return True
        if normalized in {"saltar", "skip", "ninguna"}:
            regen_instruction = ""
        else:
            regen_instruction = text.strip()
        await _save_state(
            db,
            doctor.id,
            channel_user_key,
            {
                "awaiting": "diet_regenerate_duration",
                "pending_diet_id": diet_id,
                "patient_id": patient.id,
                "regen_instruction": regen_instruction,
                "wizard_back_step": "diet_preview",
            },
        )
        await send_telegram_message(
            chat_id,
            "Antes de regenerar el borrador, indica la duración total del plan:\n"
            + _diet_duration_prompt_message(),
            reply_markup=_diet_regen_duration_choice_markup(diet_id),
        )
        return True
    if awaiting == "diet_regenerate_duration":
        diet_id = state.get("pending_diet_id")
        if not isinstance(diet_id, int):
            await _clear_state(db, doctor.id, channel_user_key)
            return False
        regen_instruction_raw = state.get("regen_instruction")
        regen_instruction = (
            regen_instruction_raw
            if isinstance(regen_instruction_raw, str)
            else ""
        )
        try:
            ddays = parse_duration_text(text)
        except DurationParseError as e:
            await send_telegram_message(
                chat_id,
                f"{e}\n\n{_diet_duration_prompt_message()}",
                reply_markup=_diet_regen_duration_choice_markup(diet_id),
            )
            return True
        await _transition_regen_duration_to_strategy(
            db,
            doctor,
            chat_id,
            channel_user_key,
            patient,
            diet_id,
            regen_instruction,
            ddays,
        )
        return True
    if awaiting == "diet_confirm":
        instruction = state.get("instruction")
        clean_instruction = (
            instruction.strip() if isinstance(instruction, str) and instruction.strip() else None
        )
        dur_raw = state.get("duration_days")
        duration_days = (
            dur_raw if isinstance(dur_raw, int) else DEFAULT_PLAN_DURATION_DAYS
        )
        if normalized in {"si", "sí", "confirmar", "ok"}:
            snap = dict(state)
            await _clear_state(db, doctor.id, channel_user_key)
            await _execute_diet_confirm_from_snapshot(
                db,
                doctor,
                chat_id,
                channel_user_key,
                patient,
                snap,
            )
            return True
        parsed_w = parse_weight(text)
        if (
            parsed_w
            and parsed_w.field == "weight_kg"
            and measurement_in_reasonable_range(parsed_w)
        ):
            await _queue_metric_confirmation(
                db,
                doctor,
                chat_id,
                channel_user_key,
                patient,
                weight_kg=parsed_w.normalized_value,
                resume_after="diet_confirm",
                resume_instruction=clean_instruction,
                resume_duration_days=duration_days,
                resume_diet_context=state,
            )
            return True
        parsed_h = parse_height(text)
        if (
            parsed_h
            and parsed_h.field == "height_cm"
            and measurement_in_reasonable_range(parsed_h)
        ):
            await _queue_metric_confirmation(
                db,
                doctor,
                chat_id,
                channel_user_key,
                patient,
                height_cm=parsed_h.normalized_value,
                resume_after="diet_confirm",
                resume_instruction=clean_instruction,
                resume_duration_days=duration_days,
                resume_diet_context=state,
            )
            return True
        intent, _, _ = await _classify_user_intent(text)
        if intent == "thanks":
            await send_telegram_message(
                chat_id,
                "Con gusto. Si quieres sigo con esta dieta: pulsa «Confirmar generación» o escribe «sí».",
                reply_markup=_diet_confirm_markup(patient.id),
            )
            return True
        if intent == "possible_mutation" and _is_height_request(text):
            hst: dict[str, Any] = {
                "awaiting": "height_cm",
                "patient_id": patient.id,
                "resume_after": "diet_confirm",
                "instruction": clean_instruction,
                "duration_days": duration_days,
            }
            hst.update(_diet_wizard_persist_slice(state))
            await _save_state(
                db,
                doctor.id,
                channel_user_key,
                hst,
            )
            await send_telegram_message(
                chat_id,
                "Perfecto. Envíame la estatura de este paciente en cm, m o pies/pulgadas.",
                reply_markup=_cancel_markup(),
            )
            return True
        if intent == "possible_mutation" and _is_weight_request(text):
            wst: dict[str, Any] = {
                "awaiting": "weight_kg",
                "patient_id": patient.id,
                "resume_after": "diet_confirm",
                "instruction": clean_instruction,
                "duration_days": duration_days,
            }
            wst.update(_diet_wizard_persist_slice(state))
            await _save_state(
                db,
                doctor.id,
                channel_user_key,
                wst,
            )
            await send_telegram_message(
                chat_id,
                "Perfecto. Envíame el peso en kg, lb o solo el número.",
                reply_markup=_cancel_markup(),
            )
            return True
        await send_telegram_message(
            chat_id,
            "Si quieres generar la dieta, pulsa «Confirmar generación» o escribe «sí». "
            "Si prefieres cambiar algo, dime por ejemplo «agregar estatura».",
            reply_markup=_diet_confirm_markup(patient.id),
        )
        return True
    if awaiting == "city":
        city = text.strip()
        if not city:
            await send_telegram_message(chat_id, "La ciudad no puede estar vacía.")
            return True
        await update_patient_fields(db, patient, city=city)
        await _clear_state(db, doctor.id, channel_user_key)
        await send_telegram_message(chat_id, f"Ciudad actualizada a {city}.")
        return True
    return False


async def _handle_callback_query(db: AsyncSession, update: dict) -> bool:
    callback = update.get("callback_query")
    if not callback:
        return False
    data = (callback.get("data") or "").strip()
    cb_id = str(callback.get("id") or "")
    from_user = callback.get("from") or {}
    message = callback.get("message") or {}
    chat = message.get("chat") or {}
    chat_id = str(chat.get("id") or "")
    user_id = str(from_user.get("id") or "")
    if not data or not chat_id or not user_id:
        if cb_id:
            await answer_telegram_callback_query(cb_id)
        return True
    doctor = await _doctor_for_telegram_user(db, user_id)
    if doctor is None:
        if cb_id:
            await answer_telegram_callback_query(cb_id, text="Primero vincula tu cuenta.")
        await send_telegram_message(
            chat_id,
            "Tu Telegram no está vinculado. En el panel genera un enlace y ábrelo aquí.",
        )
        return True

    channel_user_key = f"telegram:{user_id}"
    if _should_strip_inline_after_callback(data):
        await _try_strip_callback_inline_keyboard(chat_id, message)
    parts = data.split(":")
    if data == "noop":
        if cb_id:
            await answer_telegram_callback_query(cb_id)
        return True
    if _navigation_callback_requires_fresh_message(data):
        nav_state = await _load_state_for_update(db, doctor.id, channel_user_key)
        if not _state_message_matches(
            nav_state, key="navigation_message_id", message=message
        ):
            await _send_stale_navigation_refresh(
                db,
                doctor,
                chat_id,
                channel_user_key,
                prefix="Esa pantalla ya fue reemplazada. Te muestro la vigente.",
            )
            if cb_id:
                await answer_telegram_callback_query(cb_id)
            return True
    if data == "nav:home":
        await _send_home_screen(
            db,
            doctor,
            chat_id,
            channel_user_key,
            prefix="Menú principal:",
        )
        if cb_id:
            await answer_telegram_callback_query(cb_id)
        return True
    if data == "nav:back":
        nav_state = await _load_state(db, doctor.id, channel_user_key)
        await _send_navigation_back_target(
            db,
            doctor,
            chat_id,
            channel_user_key,
            nav_state,
            prefix="Has vuelto a la pantalla anterior.",
        )
        if cb_id:
            await answer_telegram_callback_query(cb_id)
        return True
    if len(parts) >= 3 and parts[:2] == ["flow", "pswitch"] and parts[2] == "no":
        await _save_state(
            db,
            doctor.id,
            channel_user_key,
            {
                "pending_switch_patient_id": None,
                "pending_switch_action": None,
                "pending_switch_extra": None,
            },
        )
        await send_telegram_message(chat_id, "Cambio de paciente cancelado.")
        if cb_id:
            await answer_telegram_callback_query(cb_id)
        return True
    if (
        len(parts) >= 6
        and parts[:3] == ["flow", "pswitch", "yes"]
        and parts[4].isdigit()
    ):
        action_sw = parts[3]
        patient_id_sw = int(parts[4])
        extra_sw = parts[5]
        await _save_state(
            db,
            doctor.id,
            channel_user_key,
            {
                "active_patient_id": patient_id_sw,
                "pending_switch_patient_id": None,
                "pending_switch_action": None,
                "pending_switch_extra": None,
            },
        )
        patient_sw = await get_doctor_patient(db, doctor.id, patient_id_sw)
        if not patient_sw:
            await send_telegram_message(chat_id, "Paciente no encontrado.")
        elif action_sw == "select":
            await _show_patient_card(
                db, doctor, chat_id, channel_user_key, patient_sw
            )
        elif action_sw == "diet":
            await _start_guided_diet_flow(
                db, doctor, chat_id, channel_user_key, patient_sw
            )
        elif action_sw == "history":
            page_sw = int(extra_sw) if extra_sw.isdigit() else 1
            await _send_patient_history_ui(
                db,
                doctor,
                chat_id,
                patient_id_sw,
                channel_user_key,
                page=max(1, page_sw),
            )
        elif action_sw == "weight":
            await _save_state(
                db,
                doctor.id,
                channel_user_key,
                {
                    "awaiting": "weight_kg",
                    "patient_id": patient_sw.id,
                },
            )
            await _remember_patient_context(
                db, doctor.id, channel_user_key, patient_sw.id
            )
            await send_telegram_message(
                chat_id,
                "Perfecto. Envíame el peso en kg, lb o solo el número.",
                reply_markup=_cancel_markup(),
            )
        elif action_sw == "height":
            await _save_state(
                db,
                doctor.id,
                channel_user_key,
                {
                    "awaiting": "height_cm",
                    "patient_id": patient_sw.id,
                },
            )
            await _remember_patient_context(
                db, doctor.id, channel_user_key, patient_sw.id
            )
            await send_telegram_message(
                chat_id,
                "Perfecto. Envíame la estatura de este paciente en cm, m o pies/pulgadas.",
                reply_markup=_cancel_markup(),
            )
        elif action_sw == "note" and extra_sw in ("yes", "no"):
            if extra_sw == "no":
                await _save_state(
                    db,
                    doctor.id,
                    channel_user_key,
                    {
                        "awaiting": "diet_duration",
                        "patient_id": patient_sw.id,
                        "instruction": None,
                        "wizard_back_step": "diet_note_offer",
                    },
                )
                await send_telegram_message(
                    chat_id,
                    _diet_duration_prompt_message(),
                    reply_markup=_diet_duration_choice_markup(patient_sw.id),
                )
            else:
                await _save_state(
                    db,
                    doctor.id,
                    channel_user_key,
                    {
                        "awaiting": "diet_instruction",
                        "patient_id": patient_sw.id,
                    },
                )
                await send_telegram_message(
                    chat_id,
                    "Escribe la nota o especificaciones extra para la IA (ej.: más proteína, sin mariscos). "
                    "Si cambias de idea, escribe «saltar».",
                    reply_markup=_cancel_markup(),
                )
        else:
            await send_telegram_message(chat_id, "Cambio de paciente confirmado.")
        if cb_id:
            await answer_telegram_callback_query(cb_id)
        return True
    if parts[:2] == ["menu", "help"]:
        await _send_help_screen(db, doctor, chat_id, channel_user_key)
    elif parts[:2] == ["menu", "stats"]:
        await _send_stats_screen(db, doctor, chat_id, channel_user_key)
    elif parts[:2] == ["menu", "search"]:
        await _save_state(
            db,
            doctor.id,
            channel_user_key,
            {"awaiting": "search_query"},
        )
        await send_telegram_message(
            chat_id,
            "Escribe nombre o apellido para buscar.",
            reply_markup=_cancel_markup(),
        )
    elif len(parts) >= 3 and parts[:2] == ["menu", "patients"]:
        page = int(parts[2]) if parts[2].isdigit() else 1
        query = None
        if len(parts) >= 4 and parts[3] != "_":
            query = parts[3]
        await _send_patients_page(
            db,
            doctor,
            chat_id,
            channel_user_key,
            page=max(1, page),
            query=query,
        )
    elif len(parts) >= 3 and parts[:2] == ["patient", "weight"] and parts[2].isdigit():
        patient_id_w = int(parts[2])
        if not await _guard_active_patient_switch(
            db,
            doctor,
            chat_id,
            channel_user_key,
            target_patient_id=patient_id_w,
            action="weight",
            extra="_",
        ):
            if cb_id:
                await answer_telegram_callback_query(cb_id)
            return True
        patient_w = await get_doctor_patient(db, doctor.id, patient_id_w)
        if not patient_w:
            await send_telegram_message(chat_id, "Paciente no encontrado.")
        else:
            await _remember_patient_context(
                db, doctor.id, channel_user_key, patient_id_w
            )
            await _save_state(
                db,
                doctor.id,
                channel_user_key,
                {"awaiting": "weight_kg", "patient_id": patient_w.id},
            )
            await send_telegram_message(
                chat_id,
                "Perfecto. Envíame el peso en kg, lb o solo el número.",
                reply_markup=_cancel_markup(),
            )
    elif len(parts) >= 3 and parts[:2] == ["patient", "height"] and parts[2].isdigit():
        patient_id_h = int(parts[2])
        if not await _guard_active_patient_switch(
            db,
            doctor,
            chat_id,
            channel_user_key,
            target_patient_id=patient_id_h,
            action="height",
            extra="_",
        ):
            if cb_id:
                await answer_telegram_callback_query(cb_id)
            return True
        patient_h = await get_doctor_patient(db, doctor.id, patient_id_h)
        if not patient_h:
            await send_telegram_message(chat_id, "Paciente no encontrado.")
        else:
            await _remember_patient_context(
                db, doctor.id, channel_user_key, patient_id_h
            )
            await _save_state(
                db,
                doctor.id,
                channel_user_key,
                {"awaiting": "height_cm", "patient_id": patient_h.id},
            )
            await send_telegram_message(
                chat_id,
                "Perfecto. Envíame la estatura de este paciente en cm, m o pies/pulgadas.",
                reply_markup=_cancel_markup(),
            )
    elif len(parts) >= 3 and parts[:2] == ["patient", "city"] and parts[2].isdigit():
        await send_telegram_message(chat_id, MSG_PANEL_ONLY_UPDATES, reply_markup=_menu_markup())
    elif len(parts) >= 4 and parts[:2] == ["patient", "history"] and parts[2].isdigit():
        patient_id = int(parts[2])
        page = int(parts[3]) if parts[3].isdigit() else 1
        if not await _guard_active_patient_switch(
            db,
            doctor,
            chat_id,
            channel_user_key,
            target_patient_id=patient_id,
            action="history",
            extra=str(max(1, page)),
        ):
            if cb_id:
                await answer_telegram_callback_query(cb_id)
            return True
        await _send_patient_history_ui(
            db,
            doctor,
            chat_id,
            patient_id,
            channel_user_key,
            page=max(1, page),
            back_state=_navigation_back_state("patient_card", patient_id=patient_id),
        )
    elif (
        len(parts) >= 4
        and parts[0] == "metric"
        and parts[1] == "confirm"
        and parts[2].isdigit()
        and parts[3] in ("weight", "height")
    ):
        patient_id_mc = int(parts[2])
        kind_mc = parts[3]
        st_m = await _load_state_for_update(db, doctor.id, channel_user_key)
        if st_m.get("awaiting") != "metric_confirm" or st_m.get(
            "patient_id"
        ) != patient_id_mc or not _state_message_matches(
            st_m, key="metric_confirm_message_id", message=message
        ):
            await _send_stale_step_refresh(
                db,
                doctor,
                chat_id,
                channel_user_key,
                prefix="Este paso ya no aplica.",
            )
        else:
            pw = st_m.get("pending_weight_kg")
            ph = st_m.get("pending_height_cm")
            if kind_mc == "weight" and pw is None:
                await send_telegram_message(
                    chat_id,
                    "No hay un peso pendiente de confirmar. Vuelve a enviarlo.",
                )
            elif kind_mc == "height" and ph is None:
                await send_telegram_message(
                    chat_id,
                    "No hay una estatura pendiente de confirmar. Vuelve a enviarla.",
                )
            else:
                patient_m = await get_doctor_patient(
                    db, doctor.id, patient_id_mc
                )
                if not patient_m:
                    await send_telegram_message(
                        chat_id, "Paciente no encontrado."
                    )
                else:
                    await _save_state(
                        db,
                        doctor.id,
                        channel_user_key,
                        {"metric_confirm_message_id": None},
                    )
                    if kind_mc == "weight":
                        await add_patient_metric(
                            db, patient_id_mc, weight_kg=float(pw)
                        )
                    else:
                        await add_patient_metric(
                            db, patient_id_mc, height_cm=float(ph)
                        )
                    resume = st_m.get("resume_after")
                    if resume == "diet_confirm":
                        new_st: dict[str, Any] = {
                            k: v
                            for k, v in st_m.items()
                            if k
                            not in (
                                "pending_weight_kg",
                                "pending_height_cm",
                                "awaiting",
                            )
                        }
                        new_st["awaiting"] = "diet_confirm"
                        await _save_state(
                            db, doctor.id, channel_user_key, new_st
                        )
                        if kind_mc == "height":
                            await _send_diet_confirm_prompt(
                                db,
                                doctor,
                                chat_id,
                                channel_user_key,
                                patient_m,
                                body=(
                                    "Estatura guardada. Ya puedo retomar la dieta: "
                                    "pulsa «Confirmar generación» o ajusta la configuración."
                                ),
                            )
                        else:
                            await _send_diet_confirm_prompt(
                                db,
                                doctor,
                                chat_id,
                                channel_user_key,
                                patient_m,
                                body=(
                                    "Peso guardado. Continúa con la generación: "
                                    "pulsa «Confirmar generación» o ajusta la configuración."
                                ),
                            )
                    else:
                        await _clear_state(
                            db, doctor.id, channel_user_key
                        )
                        if kind_mc == "weight":
                            await send_telegram_message(
                                chat_id,
                                f"Peso guardado: {float(pw):.2f} kg.",
                                reply_markup=_menu_markup(),
                            )
                        else:
                            await send_telegram_message(
                                chat_id,
                                f"Estatura guardada: {float(ph):.1f} cm.",
                                reply_markup=_menu_markup(),
                            )
                        await send_telegram_message(
                            chat_id,
                            _welcome_extended_block(doctor),
                            reply_markup=_menu_markup(),
                        )
    elif (
        len(parts) >= 3
        and parts[0] == "metric"
        and parts[1] == "cancel"
        and parts[2].isdigit()
    ):
        patient_id_mx = int(parts[2])
        st_x = await _load_state_for_update(db, doctor.id, channel_user_key)
        if st_x.get("awaiting") != "metric_confirm" or st_x.get(
            "patient_id"
        ) != patient_id_mx or not _state_message_matches(
            st_x, key="metric_confirm_message_id", message=message
        ):
            await _send_stale_step_refresh(
                db,
                doctor,
                chat_id,
                channel_user_key,
                prefix="Este paso ya no aplica.",
            )
        else:
            resume_x = st_x.get("resume_after")
            if resume_x == "diet_confirm":
                new_x: dict[str, Any] = {
                    k: v
                    for k, v in st_x.items()
                    if k
                    not in (
                        "pending_weight_kg",
                        "pending_height_cm",
                        "awaiting",
                    )
                }
                new_x["awaiting"] = "diet_confirm"
                await _save_state(
                    db, doctor.id, channel_user_key, new_x
                )
                patient_mx = await get_doctor_patient(db, doctor.id, patient_id_mx)
                if patient_mx:
                    await _send_diet_confirm_prompt(
                        db,
                        doctor,
                        chat_id,
                        channel_user_key,
                        patient_mx,
                        body=(
                            "Cambio de peso/estatura cancelado. Sigue con la "
                            "generación con los botones de abajo."
                        ),
                    )
                else:
                    await send_telegram_message(
                        chat_id,
                        "Cambio de peso/estatura cancelado.",
                        reply_markup=_menu_markup(),
                    )
            else:
                await _clear_state(db, doctor.id, channel_user_key)
                await send_telegram_message(
                    chat_id,
                    "Cambio cancelado.",
                    reply_markup=_menu_markup(),
                )
    elif len(parts) >= 3 and parts[:2] == ["patient", "diet"] and parts[2].isdigit():
        patient_id = int(parts[2])
        if not await _guard_active_patient_switch(
            db,
            doctor,
            chat_id,
            channel_user_key,
            target_patient_id=patient_id,
            action="diet",
            extra="_",
        ):
            if cb_id:
                await answer_telegram_callback_query(cb_id)
            return True
        patient = await get_doctor_patient(db, doctor.id, patient_id)
        if patient:
            st_diet = await _load_state(db, doctor.id, channel_user_key)
            if _has_active_diet_wizard_for_patient(st_diet, patient_id):
                await _send_stale_step_refresh(
                    db,
                    doctor,
                    chat_id,
                    channel_user_key,
                    prefix="Ya tienes un flujo de dieta abierto para este paciente.",
                )
            else:
                await _start_guided_diet_flow(
                    db, doctor, chat_id, channel_user_key, patient
                )
    elif len(parts) >= 4 and parts[:2] == ["patient", "archive"] and parts[2].isdigit():
        await send_telegram_message(chat_id, MSG_PANEL_ONLY_UPDATES, reply_markup=_menu_markup())
    elif len(parts) >= 3 and parts[:2] == ["patient", "select"] and parts[2].isdigit():
        patient_id = int(parts[2])
        if not await _guard_active_patient_switch(
            db,
            doctor,
            chat_id,
            channel_user_key,
            target_patient_id=patient_id,
            action="select",
            extra="_",
        ):
            if cb_id:
                await answer_telegram_callback_query(cb_id)
            return True
        patient = await get_doctor_patient(db, doctor.id, patient_id)
        if patient:
            current_nav = await _load_state(db, doctor.id, channel_user_key)
            current_screen = current_nav.get("navigation_screen")
            if current_screen == "patients":
                back_state = _navigation_back_state(
                    "patients",
                    page=current_nav.get("navigation_page")
                    if isinstance(current_nav.get("navigation_page"), int)
                    else 1,
                    query=current_nav.get("navigation_query")
                    if isinstance(current_nav.get("navigation_query"), str)
                    else None,
                )
            elif current_screen == "patient_picker":
                back_state = _navigation_back_state_from_context(current_nav)
            else:
                back_state = _navigation_back_state("home")
            await _show_patient_card(
                db,
                doctor,
                chat_id,
                channel_user_key,
                patient,
                back_state=back_state,
            )
    elif len(parts) >= 3 and parts[:2] == ["diet", "pdf"] and parts[2].isdigit():
        diet = await db.get(Diet, int(parts[2]))
        if diet is None or diet.doctor_id != doctor.id:
            await send_telegram_message(chat_id, "Dieta no encontrada.")
        else:
            await _send_diet_pdf(db, doctor, chat_id, diet)
    elif (
        len(parts) >= 4
        and parts[0] == "diet"
        and parts[1] == "note"
        and parts[2] in ("yes", "no")
        and parts[3].isdigit()
    ):
        patient_id = int(parts[3])
        note_state = await _load_state_for_update(db, doctor.id, channel_user_key)
        if (
            note_state.get("awaiting") != "diet_note_offer"
            or note_state.get("patient_id") != patient_id
            or not _wizard_inline_matches(note_state, message)
        ):
            await _send_stale_step_refresh(
                db,
                doctor,
                chat_id,
                channel_user_key,
                prefix="Este paso ya no aplica.",
            )
            if cb_id:
                await answer_telegram_callback_query(cb_id)
            return True
        if not await _guard_active_patient_switch(
            db,
            doctor,
            chat_id,
            channel_user_key,
            target_patient_id=patient_id,
            action="note",
            extra=parts[2],
        ):
            if cb_id:
                await answer_telegram_callback_query(cb_id)
            return True
        patient = await get_doctor_patient(db, doctor.id, patient_id)
        if not patient:
            await send_telegram_message(chat_id, "Paciente no encontrado.")
        elif parts[2] == "no":
            await _send_wizard_inline_prompt(
                db,
                doctor,
                chat_id,
                channel_user_key,
                text=_diet_duration_prompt_message(),
                reply_markup=_diet_duration_choice_markup(patient.id),
                state_patch={
                    "awaiting": "diet_duration",
                    "patient_id": patient.id,
                    "instruction": None,
                    "wizard_back_step": "diet_note_offer",
                },
            )
        else:
            await _save_state(
                db,
                doctor.id,
                channel_user_key,
                {
                    "awaiting": "diet_instruction",
                    "patient_id": patient.id,
                },
            )
            await send_telegram_message(
                chat_id,
                "Escribe la nota o especificaciones extra para la IA (ej.: más proteína, sin mariscos). "
                "Si cambias de idea, escribe «saltar».",
                reply_markup=_cancel_markup(),
            )
    elif (
        len(parts) == 4
        and parts[0] == "diet"
        and parts[1] == "pickdur"
        and parts[2].isdigit()
        and parts[3].isdigit()
    ):
        patient_id_cb = int(parts[2])
        ddays_cb = int(parts[3])
        state_cb = await _load_state_for_update(db, doctor.id, channel_user_key)
        if (
            state_cb.get("awaiting") != "diet_duration"
            or state_cb.get("patient_id") != patient_id_cb
            or not _wizard_inline_matches(state_cb, message)
        ):
            await _send_stale_step_refresh(
                db,
                doctor,
                chat_id,
                channel_user_key,
                prefix="Este paso ya no aplica.",
            )
        else:
            patient_cb = await get_doctor_patient(db, doctor.id, patient_id_cb)
            if not patient_cb:
                await send_telegram_message(chat_id, "Paciente no encontrado.")
            else:
                instr_cb = state_cb.get("instruction")
                await _transition_new_diet_duration_to_strategy(
                    db,
                    doctor,
                    chat_id,
                    channel_user_key,
                    patient_cb,
                    instr_cb if isinstance(instr_cb, str) else None,
                    ddays_cb,
                )
    elif (
        len(parts) == 4
        and parts[0] == "diet"
        and parts[1] == "pickrdur"
        and parts[2].isdigit()
        and parts[3].isdigit()
    ):
        diet_id_cb = int(parts[2])
        ddays_cb = int(parts[3])
        state_cb = await _load_state_for_update(db, doctor.id, channel_user_key)
        if (
            state_cb.get("awaiting") != "diet_regenerate_duration"
            or state_cb.get("pending_diet_id") != diet_id_cb
            or not _wizard_inline_matches(state_cb, message)
        ):
            await _send_stale_step_refresh(
                db,
                doctor,
                chat_id,
                channel_user_key,
                prefix="Este paso ya no aplica.",
            )
        else:
            pid_cb = state_cb.get("patient_id")
            if not isinstance(pid_cb, int):
                await _clear_state(db, doctor.id, channel_user_key)
                await send_telegram_message(
                    chat_id,
                    "No pude continuar. Inicia de nuevo el flujo.",
                    reply_markup=_menu_markup(),
                )
            else:
                patient_cb = await get_doctor_patient(db, doctor.id, pid_cb)
                if not patient_cb:
                    await send_telegram_message(chat_id, "Paciente no encontrado.")
                else:
                    regen_raw = state_cb.get("regen_instruction")
                    regen_cb = (
                        regen_raw if isinstance(regen_raw, str) else ""
                    )
                    await _transition_regen_duration_to_strategy(
                        db,
                        doctor,
                        chat_id,
                        channel_user_key,
                        patient_cb,
                        diet_id_cb,
                        regen_cb,
                        ddays_cb,
                    )
    elif (
        len(parts) == 4
        and parts[0] == "diet"
        and parts[1] == "meals"
        and parts[2] in ("2", "3", "4", "5")
        and parts[3].isdigit()
    ):
        await _handle_diet_meals_callback(
            db,
            doctor,
            chat_id,
            channel_user_key,
            patient_id_cb=int(parts[3]),
            meals_per_day=int(parts[2]),
            message=message,
        )
    elif (
        len(parts) == 4
        and parts[0] == "diet"
        and parts[1] == "smd"
        and parts[3].isdigit()
        and parts[2] in ("a", "g", "m")
    ):
        await _handle_diet_smd_callback(
            db,
            doctor,
            chat_id,
            channel_user_key,
            patient_id_cb=int(parts[3]),
            letter=parts[2],
            message=message,
        )
    elif (
        len(parts) == 4
        and parts[0] == "diet"
        and parts[1] == "sty"
        and parts[3].isdigit()
        and len(parts[2]) == 1
    ):
        await _handle_diet_sty_callback(
            db,
            doctor,
            chat_id,
            channel_user_key,
            code=parts[2],
            patient_id_cb=int(parts[3]),
            message=message,
        )
    elif (
        len(parts) == 3
        and parts[0] == "diet"
        and parts[1] in ("mp", "mc", "mf")
        and len(parts[2]) == 1
    ):
        await _handle_diet_macro_callback(
            db,
            doctor,
            chat_id,
            channel_user_key,
            which=parts[1],
            letter=parts[2],
            message=message,
        )
    elif (
        len(parts) == 4
        and parts[0] == "diet"
        and parts[1] == "preview"
        and parts[2] in ("fulldays", "editpick", "resume")
        and parts[3].isdigit()
    ):
        diet_id = int(parts[3])
        diet = await db.get(Diet, diet_id)
        if diet is None or diet.doctor_id != doctor.id:
            await send_telegram_message(chat_id, "Dieta no encontrada.")
        elif diet.status != "pending_approval":
            await send_telegram_message(
                chat_id,
                "Este borrador ya no está pendiente de aprobación.",
                reply_markup=_menu_markup(),
            )
        else:
            conv_state = await _load_state(db, doctor.id, channel_user_key)
            if not _preview_session_matches(conv_state, diet_id):
                await _send_stale_step_refresh(
                    db,
                    doctor,
                    chat_id,
                    channel_user_key,
                    prefix="Este paso ya no aplica.",
                )
            elif parts[2] == "resume":
                patient = await get_doctor_patient(db, doctor.id, diet.patient_id)
                if patient:
                    await _send_diet_preview_and_store_state(
                        db,
                        doctor,
                        chat_id,
                        channel_user_key,
                        diet,
                        patient,
                        doctor_note=diet.notes,
                    )
                else:
                    await send_telegram_message(chat_id, "Paciente no encontrado.")
            elif parts[2] == "fulldays":
                raw_plan = diet.structured_plan_json
                plan: dict[str, Any] = (
                    raw_plan if isinstance(raw_plan, dict) else {}
                )
                days = plan.get("days")
                num_days = len(days) if isinstance(days, list) and days else 1
                if (
                    not isinstance(days, list)
                    or not days
                    or not all(isinstance(d, dict) for d in days)
                ):
                    await send_telegram_message(
                        chat_id,
                        "Todavía no hay días estructurados en este plan.",
                    )
                else:
                    await _send_telegram_diet_fulldays(
                        chat_id, plan, num_days
                    )
                    await send_telegram_message(
                        chat_id,
                        "Puedes volver al resumen o editar una comida.",
                        reply_markup={
                            "inline_keyboard": [
                                [
                                    {
                                        "text": "Resumen",
                                        "callback_data": f"diet:preview:resume:{diet_id}",
                                    },
                                    {
                                        "text": "Editar comida",
                                        "callback_data": f"diet:preview:editpick:{diet_id}",
                                    },
                                ]
                            ]
                        },
                    )
            else:
                raw_plan2 = diet.structured_plan_json
                plan2: dict[str, Any] = (
                    raw_plan2 if isinstance(raw_plan2, dict) else {}
                )
                dlist = plan2.get("days")
                num_d = (
                    len(dlist) if isinstance(dlist, list) and dlist else 1
                )
                if (
                    not isinstance(dlist, list)
                    or not dlist
                    or not all(isinstance(d, dict) for d in dlist)
                ):
                    await send_telegram_message(
                        chat_id,
                        "Todavía no hay días estructurados en este plan.",
                    )
                else:
                    n_btns = min(num_d, 14)
                    cap_note = f" (primeros {n_btns} días)" if num_d > 14 else ""
                    mid = await send_telegram_message(
                        chat_id,
                        f"Editar comida: elige el día (1–{n_btns}){cap_note}.",
                        reply_markup=_diet_edit_day_inline_keyboard(
                            diet_id, n_btns
                        ),
                    )
                    await _save_state(
                        db,
                        doctor.id,
                        channel_user_key,
                        {
                            "edit_day_message_id": mid,
                            "edit_slot_message_id": None,
                        },
                    )
    elif (
        len(parts) == 5
        and parts[0] == "diet"
        and parts[1] == "edsl"
        and parts[2].isdigit()
        and parts[3].isdigit()
        and parts[4].isdigit()
    ):
        diet_id = int(parts[2])
        day_1 = int(parts[3])
        slot_i = int(parts[4])
        diet = await db.get(Diet, diet_id)
        if diet is None or diet.doctor_id != doctor.id:
            await send_telegram_message(chat_id, "Dieta no encontrada.")
        elif diet.status != "pending_approval":
            await send_telegram_message(
                chat_id,
                "Este borrador ya no está pendiente de aprobación.",
                reply_markup=_menu_markup(),
            )
        else:
            cstate = await _load_state(db, doctor.id, channel_user_key)
            if not _preview_session_matches(cstate, diet_id):
                await _send_stale_step_refresh(
                    db,
                    doctor,
                    chat_id,
                    channel_user_key,
                    prefix="Este paso ya no aplica.",
                )
            elif not _state_message_matches(
                cstate, key="edit_slot_message_id", message=message
            ):
                await _send_stale_step_refresh(
                    db,
                    doctor,
                    chat_id,
                    channel_user_key,
                    prefix="Ese selector de comida ya fue reemplazado.",
                )
            else:
                rawp = diet.structured_plan_json
                if not isinstance(rawp, dict):
                    await send_telegram_message(
                        chat_id, "No hay estructura de plan para editar."
                    )
                else:
                    dld = rawp.get("days")
                    n_d = len(dld) if isinstance(dld, list) else 0
                    if day_1 < 1 or day_1 > n_d or n_d < 1:
                        await send_telegram_message(
                            chat_id, "Ese número de día no existe en el plan."
                        )
                    else:
                        slots = resolve_plan_meal_slots(rawp)
                        if (
                            slot_i < 0
                            or slot_i >= len(slots)
                        ):
                            await send_telegram_message(
                                chat_id, "Esa comida o día no es válido en este plan."
                            )
                        else:
                            label = meal_slot_label_es(slots[slot_i])
                            await _save_state(
                                db,
                                doctor.id,
                                channel_user_key,
                                {
                                    "awaiting": "diet_tg_edit_meal",
                                    "pending_diet_id": diet_id,
                                    "patient_id": diet.patient_id,
                                    "edit_meal_day": day_1,
                                    "edit_meal_slot_index": slot_i,
                                    "edit_day_message_id": None,
                                    "edit_slot_message_id": None,
                                },
                            )
                            await send_telegram_message(
                                chat_id,
                                f"Escribe el texto para {label} del día {day_1}. "
                                f"Máximo {_DIET_TG_MEAL_TEXT_MAX} caracteres. "
                                "«Cancelar» del teclado o la palabra «cancelar» vuelve a la vista previa.",
                                reply_markup=_cancel_markup(),
                            )
    elif (
        len(parts) == 4
        and parts[0] == "diet"
        and parts[1] == "edday"
        and parts[2].isdigit()
        and parts[3].isdigit()
    ):
        diet_id = int(parts[2])
        day_1 = int(parts[3])
        diet = await db.get(Diet, diet_id)
        if diet is None or diet.doctor_id != doctor.id:
            await send_telegram_message(chat_id, "Dieta no encontrada.")
        elif diet.status != "pending_approval":
            await send_telegram_message(
                chat_id,
                "Este borrador ya no está pendiente de aprobación.",
                reply_markup=_menu_markup(),
            )
        else:
            cstate2 = await _load_state(db, doctor.id, channel_user_key)
            if not _preview_session_matches(cstate2, diet_id):
                await _send_stale_step_refresh(
                    db,
                    doctor,
                    chat_id,
                    channel_user_key,
                    prefix="Este paso ya no aplica.",
                )
            elif not _state_message_matches(
                cstate2, key="edit_day_message_id", message=message
            ):
                await _send_stale_step_refresh(
                    db,
                    doctor,
                    chat_id,
                    channel_user_key,
                    prefix="Ese selector de dia ya fue reemplazado.",
                )
            else:
                rawp2 = diet.structured_plan_json
                if not isinstance(rawp2, dict):
                    await send_telegram_message(
                        chat_id, "No hay estructura de plan para editar."
                    )
                else:
                    dlist2 = rawp2.get("days")
                    nlen = len(dlist2) if isinstance(dlist2, list) else 0
                    if nlen < 1 or not isinstance(dlist2, list):
                        await send_telegram_message(
                            chat_id, "Todavía no hay días estructurados en este plan."
                        )
                    elif day_1 < 1 or day_1 > nlen:
                        await send_telegram_message(
                            chat_id, "Ese número de día no existe en el plan."
                        )
                    else:
                        slots2 = resolve_plan_meal_slots(rawp2)
                        if not slots2:
                            await send_telegram_message(
                                chat_id, "No hay comidas por día en este plan."
                            )
                        else:
                            mid = await send_telegram_message(
                                chat_id,
                                f"Día {day_1} — elige qué comida reemplazar:",
                                reply_markup=_diet_edit_slot_inline_keyboard(
                                    diet_id, day_1, slots2
                                ),
                            )
                            await _save_state(
                                db,
                                doctor.id,
                                channel_user_key,
                                {"edit_slot_message_id": mid},
                            )
    elif (
        len(parts) >= 4
        and parts[0] == "diet"
        and parts[1] == "preview"
        and parts[2] in ("approve", "discard", "regen", "quickmenu", "reshow")
        and parts[3].isdigit()
    ):
        diet_id = int(parts[3])
        diet = await db.get(Diet, diet_id)
        if diet is None or diet.doctor_id != doctor.id:
            await send_telegram_message(chat_id, "Dieta no encontrada.")
        elif diet.status != "pending_approval":
            await send_telegram_message(
                chat_id,
                "Este borrador ya no está pendiente de aprobación.",
                reply_markup=_menu_markup(),
            )
        else:
            conv_state = await _load_state(db, doctor.id, channel_user_key)
            act = parts[2]
            strict_preview = act in (
                "approve",
                "discard",
                "regen",
                "quickmenu",
            )
            if strict_preview and not _preview_session_matches(
                conv_state, diet_id
            ):
                await _send_stale_step_refresh(
                    db,
                    doctor,
                    chat_id,
                    channel_user_key,
                    prefix="Este paso ya no aplica.",
                )
            elif not _state_message_matches(
                conv_state, key="preview_message_id", message=message
            ):
                await _send_stale_step_refresh(
                    db,
                    doctor,
                    chat_id,
                    channel_user_key,
                    prefix="Este mensaje ya fue reemplazado por otro más reciente.",
                )
            elif act == "quickmenu":
                await _save_state(
                    db,
                    doctor.id,
                    channel_user_key,
                    {"preview_message_id": None},
                )
                await _send_diet_quick_adjust_menu(
                    db,
                    doctor,
                    chat_id,
                    channel_user_key,
                    diet_id,
                )
            elif act == "reshow":
                patient = await get_doctor_patient(db, doctor.id, diet.patient_id)
                if patient:
                    await _send_diet_preview_and_store_state(
                        db,
                        doctor,
                        chat_id,
                        channel_user_key,
                        diet,
                        patient,
                        doctor_note=diet.notes,
                    )
                else:
                    await send_telegram_message(chat_id, "Paciente no encontrado.")
            elif act == "approve":
                conv_state = await _load_state_for_update(
                    db, doctor.id, channel_user_key
                )
                if (
                    not _preview_session_matches(conv_state, diet_id)
                    or not _state_message_matches(
                        conv_state, key="preview_message_id", message=message
                    )
                ):
                    await _send_stale_step_refresh(
                        db,
                        doctor,
                        chat_id,
                        channel_user_key,
                        prefix="Este paso ya no aplica.",
                    )
                    if cb_id:
                        await answer_telegram_callback_query(cb_id)
                    return True
                await _save_state(
                    db,
                    doctor.id,
                    channel_user_key,
                    {
                        "preview_message_id": None,
                        "quick_adjust_message_id": None,
                    },
                )
                try:
                    diet = await approve_diet_preview(db, doctor, diet_id)
                except DietGenerationError:
                    await send_telegram_message(
                        chat_id,
                        "No pude aprobar el borrador.",
                        reply_markup=_menu_markup(),
                    )
                else:
                    patient = await get_doctor_patient(
                        db, doctor.id, diet.patient_id
                    )
                    await _clear_state(db, doctor.id, channel_user_key)
                    await send_telegram_message(
                        chat_id,
                        f"Dieta #{diet_id} aprobada. Envío el PDF.",
                    )
                    if patient:
                        await _send_diet_pdf(
                            db, doctor, chat_id, diet, patient=patient
                        )
            elif act == "discard":
                conv_state = await _load_state_for_update(
                    db, doctor.id, channel_user_key
                )
                if (
                    not _preview_session_matches(conv_state, diet_id)
                    or not _state_message_matches(
                        conv_state, key="preview_message_id", message=message
                    )
                ):
                    await _send_stale_step_refresh(
                        db,
                        doctor,
                        chat_id,
                        channel_user_key,
                        prefix="Este paso ya no aplica.",
                    )
                    if cb_id:
                        await answer_telegram_callback_query(cb_id)
                    return True
                await _save_state(
                    db,
                    doctor.id,
                    channel_user_key,
                    {
                        "preview_message_id": None,
                        "quick_adjust_message_id": None,
                    },
                )
                try:
                    await discard_diet_preview(db, doctor, diet_id)
                except DietGenerationError:
                    await send_telegram_message(
                        chat_id,
                        "No pude descartar el borrador.",
                        reply_markup=_menu_markup(),
                    )
                else:
                    await _clear_state(db, doctor.id, channel_user_key)
                    await send_telegram_message(
                        chat_id,
                        "Borrador descartado.",
                        reply_markup=_menu_markup(),
                    )
            else:
                conv_state = await _load_state_for_update(
                    db, doctor.id, channel_user_key
                )
                if (
                    not _preview_session_matches(conv_state, diet_id)
                    or not _state_message_matches(
                        conv_state, key="preview_message_id", message=message
                    )
                ):
                    await _send_stale_step_refresh(
                        db,
                        doctor,
                        chat_id,
                        channel_user_key,
                        prefix="Este paso ya no aplica.",
                    )
                    if cb_id:
                        await answer_telegram_callback_query(cb_id)
                    return True
                await _save_state(
                    db,
                    doctor.id,
                    channel_user_key,
                    {
                        "preview_message_id": None,
                        "quick_adjust_message_id": None,
                    },
                )
                await _save_state(
                    db,
                    doctor.id,
                    channel_user_key,
                    {
                        "awaiting": "diet_regenerate_note",
                        "pending_diet_id": diet_id,
                        "patient_id": diet.patient_id,
                    },
                )
                await send_telegram_message(
                    chat_id,
                    "Envía la nueva nota o especificaciones para regenerar el plan. "
                    "Escribe «saltar» para orientar solo con los datos del paciente.",
                    reply_markup=_cancel_markup(),
                )
    elif (
        len(parts) >= 4
        and parts[0] == "diet"
        and parts[1] == "quick"
        and parts[3].isdigit()
    ):
        diet_id = int(parts[3])
        code = parts[2]
        diet = await db.get(Diet, diet_id)
        if diet is None or diet.doctor_id != doctor.id:
            await send_telegram_message(chat_id, "Dieta no encontrada.")
        elif diet.status != "pending_approval":
            await send_telegram_message(
                chat_id,
                "Este borrador ya no está pendiente de aprobación.",
                reply_markup=_menu_markup(),
            )
        else:
            conv_quick = await _load_state_for_update(
                db, doctor.id, channel_user_key
            )
            if not _preview_session_matches(conv_quick, diet_id):
                await _send_stale_step_refresh(
                    db,
                    doctor,
                    chat_id,
                    channel_user_key,
                    prefix="Este paso ya no aplica.",
                )
            elif not _state_message_matches(
                conv_quick, key="quick_adjust_message_id", message=message
            ):
                await _send_stale_step_refresh(
                    db,
                    doctor,
                    chat_id,
                    channel_user_key,
                    prefix="Ese menú de ajustes ya fue reemplazado.",
                )
            elif code not in _DIET_QUICK_ADJUST:
                await send_telegram_message(
                    chat_id, "Opción de ajuste no reconocida."
                )
            else:
                await _save_state(
                    db,
                    doctor.id,
                    channel_user_key,
                    {
                        "preview_message_id": None,
                        "quick_adjust_message_id": None,
                    },
                )
                merged = _merge_note_with_quick_adjust(diet.notes, code)
                try:
                    diet = await regenerate_diet(
                        db,
                        doctor,
                        diet_id,
                        merged,
                        diet_status="pending_approval",
                    )
                except DietGenerationError as e:
                    msg = "\n".join(e.reasons) if e.reasons else e.message
                    await send_telegram_message(chat_id, msg[:4090])
                else:
                    patient = await get_doctor_patient(
                        db, doctor.id, diet.patient_id
                    )
                    if not patient:
                        await send_telegram_message(
                            chat_id, "Paciente no encontrado."
                        )
                    else:
                        await _send_diet_preview_and_store_state(
                            db,
                            doctor,
                            chat_id,
                            channel_user_key,
                            diet,
                            patient,
                            doctor_note=diet.notes,
                        )
    elif len(parts) >= 3 and parts[:2] == ["diet", "confirm"] and parts[2].isdigit():
        patient_id = int(parts[2])
        patient = await get_doctor_patient(db, doctor.id, patient_id)
        state = await _load_state_for_update(db, doctor.id, channel_user_key)
        if (
            state.get("awaiting") != "diet_confirm"
            or state.get("patient_id") != patient_id
            or not _state_message_matches(
                state, key="confirm_message_id", message=message
            )
        ):
            await _send_stale_step_refresh(
                db,
                doctor,
                chat_id,
                channel_user_key,
                prefix="Este paso ya no aplica.",
            )
            if cb_id:
                await answer_telegram_callback_query(cb_id)
            return True
        snap_cb = dict(state)
        await _clear_state(db, doctor.id, channel_user_key)
        if not patient:
            await send_telegram_message(chat_id, "Paciente no encontrado.")
        else:
            await _execute_diet_confirm_from_snapshot(
                db,
                doctor,
                chat_id,
                channel_user_key,
                patient,
                snap_cb,
            )
    elif data == "flow:refresh":
        await _send_stale_step_refresh(
            db,
            doctor,
            chat_id,
            channel_user_key,
            prefix="Te muestro el paso vigente.",
        )
    elif data == "flow:back":
        st_back = await _load_state(db, doctor.id, channel_user_key)
        back_step = st_back.get("wizard_back_step")
        awaiting_back = st_back.get("awaiting")
        patient_id_back = st_back.get("patient_id")
        if (
            awaiting_back == "diet_note_offer"
            and isinstance(patient_id_back, int)
            and not isinstance(back_step, str)
        ):
            patient_back = await get_doctor_patient(
                db, doctor.id, patient_id_back
            )
            if patient_back:
                await _save_state(
                    db,
                    doctor.id,
                    channel_user_key,
                    {
                        "awaiting": None,
                        "wizard_inline_message_id": None,
                        "confirm_message_id": None,
                        "wizard_back_step": None,
                    },
                )
                await _show_patient_card(
                    db,
                    doctor,
                    chat_id,
                    channel_user_key,
                    patient_back,
                    prefix="Has vuelto a la ficha del paciente.",
                )
                if cb_id:
                    await answer_telegram_callback_query(cb_id)
                return True
        if not isinstance(back_step, str) or not back_step:
            await _send_stale_step_refresh(
                db,
                doctor,
                chat_id,
                channel_user_key,
                prefix="No hay un paso anterior disponible. Te muestro el paso vigente.",
            )
        else:
            await _save_state(
                db,
                doctor.id,
                channel_user_key,
                {
                    "awaiting": back_step,
                    "wizard_inline_message_id": None,
                    "confirm_message_id": None,
                },
            )
            await _send_stale_step_refresh(
                db,
                doctor,
                chat_id,
                channel_user_key,
                prefix="Has vuelto al paso anterior.",
            )
    elif data == "flow:cancel":
        stc = await _load_state(db, doctor.id, channel_user_key)
        if stc.get("awaiting") == "diet_tg_edit_meal" and isinstance(
            stc.get("pending_diet_id"), int
        ):
            did = stc.get("pending_diet_id")
            pat = stc.get("patient_id")
            upd: dict[str, Any] = {
                "awaiting": "diet_preview",
                "pending_diet_id": did,
            }
            if isinstance(pat, int):
                upd["patient_id"] = pat
            await _save_state(db, doctor.id, channel_user_key, upd)
            await send_telegram_message(
                chat_id,
                "Edición cancelada. Sigue con la vista previa.",
                reply_markup=_diet_preview_markup(did),
            )
        else:
            await _clear_state(db, doctor.id, channel_user_key)
            await send_telegram_message(
                chat_id, "Flujo cancelado.", reply_markup=_menu_markup()
            )
    elif (
        len(parts) >= 3
        and parts[:2] == ["diet", "cancel"]
        and parts[2].isdigit()
    ):
        await _clear_state(db, doctor.id, channel_user_key)
        await send_telegram_message(
            chat_id, "Flujo cancelado.", reply_markup=_menu_markup()
        )
    if cb_id:
        await answer_telegram_callback_query(cb_id)
    return True


async def handle_telegram_update(db: AsyncSession, update: dict) -> None:
    if await _handle_callback_query(db, update):
        return

    message = update.get("message") or update.get("edited_message")
    if not message:
        return

    chat = message.get("chat") or {}
    from_user = message.get("from")
    if not from_user or chat.get("type") != "private":
        return

    chat_id = str(chat["id"])
    text = (message.get("text") or "").strip()
    if not text:
        return

    parts = text.split(maxsplit=1)
    raw_cmd = parts[0].lower()
    cmd = raw_cmd.split("@", 1)[0]
    rest = parts[1] if len(parts) > 1 else ""

    if cmd.startswith("/start"):
        arg = rest.strip()
        if arg:
            ok, reply = await _complete_bind(db, arg, from_user, chat_id)
            await send_telegram_message(chat_id, reply)
            if ok:
                doctor_bound = await _doctor_for_telegram_user(
                    db, str(from_user["id"])
                )
                if doctor_bound:
                    uid = str(from_user["id"])
                    user_key = f"telegram:{uid}"
                    await _save_state(
                        db,
                        doctor_bound.id,
                        user_key,
                        {"welcome_shown": True},
                    )
                    await _send_home_screen(
                        db, doctor_bound, chat_id, user_key
                    )
            return
        doctor_start = await _doctor_for_telegram_user(db, str(from_user["id"]))
        if doctor_start:
            await _send_home_screen(
                db,
                doctor_start,
                chat_id,
                f"telegram:{from_user['id']}",
                prefix=(
                    f"Hola, {_doctor_greeting_name(doctor_start)}. "
                    "Usa el menú o escribe lo que necesites."
                ),
            )
        else:
            await send_telegram_message(
                chat_id,
                "Para vincular tu cuenta, abre el enlace del panel como /start CODIGO.",
            )
        return

    doctor = await _doctor_for_telegram_user(db, str(from_user["id"]))
    if doctor is None:
        await send_telegram_message(
            chat_id,
            "Tu Telegram no está vinculado. En el panel: Telegram → Generate link, "
            "abre el enlace en este chat y pulsa Iniciar.",
        )
        return

    user_key = f"telegram:{from_user['id']}"
    if not text.startswith("/") and await _handle_stateful_text(
        db, doctor, chat_id, user_key, text
    ):
        return
    if not text.startswith("/"):
        st0 = await _load_state(db, doctor.id, user_key)
        first_interaction = not st0.get("welcome_shown")
        if first_interaction:
            await _maybe_send_first_welcome(db, doctor, chat_id, user_key)
        intent, policy, entities = await _classify_user_intent(text)
        if first_interaction and intent == "greeting":
            return
        if intent == "greeting":
            await _send_home_screen(
                db,
                doctor,
                chat_id,
                user_key,
                prefix=f"Hola, {_doctor_greeting_name(doctor)}. ¿En qué puedo ayudarte?",
            )
            return
        if intent == "thanks":
            await _send_home_screen(
                db,
                doctor,
                chat_id,
                user_key,
                prefix=(
                    "Con gusto. Si quieres, puedo seguir con pacientes, "
                    "estadísticas o una nueva dieta."
                ),
            )
            return
        if intent == "patients":
            await _send_patients_page(db, doctor, chat_id, user_key, page=1)
            return
        if intent == "stats_patients":
            stats = await doctor_patient_stats(db, doctor.id)
            await send_telegram_message(
                chat_id, f"Total pacientes: {stats['total']}"
            )
            return
        if intent == "stats_diets":
            n = await doctor_diet_count(db, doctor.id)
            await send_telegram_message(
                chat_id, f"Dietas generadas en el sistema: {n}"
            )
            return
        if intent == "stats_summary":
            await _send_stats_screen(db, doctor, chat_id, user_key)
            return
        if intent == "search":
            await _save_state(
                db,
                doctor.id,
                user_key,
                {"awaiting": "search_query"},
            )
            await send_telegram_message(
                chat_id,
                "Escribe nombre o apellido para buscar.",
                reply_markup=_cancel_markup(),
            )
            return
        if intent == "help":
            await _send_help_screen(db, doctor, chat_id, user_key)
            return
        if intent == "menu":
            await _send_home_screen(
                db,
                doctor,
                chat_id,
                user_key,
                prefix="Menú principal:",
            )
            return
        if intent == "diet":
            hint = _patient_name_hint(text, entities)
            if not hint.strip():
                last_patient = await _last_active_patient(db, doctor, user_key)
                if last_patient is not None:
                    await send_telegram_message(
                        chat_id,
                        f"Entendí que quieres crear una dieta. Tomaré como contexto a "
                        f"{last_patient.first_name} {last_patient.last_name}.",
                    )
                    await _start_guided_diet_flow(
                        db, doctor, chat_id, user_key, last_patient
                    )
                    return
                await send_telegram_message(
                    chat_id,
                    "Entendí que quieres crear una dieta. Primero elige el paciente o dime su nombre.",
                    reply_markup=_menu_markup(),
                )
                await _send_patients_page(db, doctor, chat_id, user_key, page=1)
                return
            patient, err, amb = await _resolve_patient_for_doctor(db, doctor, hint)
            if amb is not None:
                await _send_ambiguous_patient_buttons(
                    db,
                    doctor,
                    chat_id,
                    user_key,
                    amb,
                    back_state=_navigation_current_state(st0),
                )
                return
            if err or patient is None:
                await send_telegram_message(
                    chat_id,
                    "Entendí que quieres crear una dieta. Elige el paciente o escríbeme el nombre completo.",
                    reply_markup=_menu_markup(),
                )
                await _send_patients_page(db, doctor, chat_id, user_key, page=1)
                return
            await _start_guided_diet_flow(
                db, doctor, chat_id, user_key, patient
            )
            return
        if intent == "patient_history":
            hint = _patient_name_hint(text, entities)
            if not hint.strip():
                last_patient = await _last_active_patient(db, doctor, user_key)
                if last_patient is not None:
                    await _remember_patient_context(
                        db, doctor.id, user_key, last_patient.id
                    )
                    await _send_patient_history_ui(
                        db, doctor, chat_id, last_patient.id, user_key
                    )
                    return
                await send_telegram_message(
                    chat_id,
                    "Indica el nombre o número del paciente para ver su historial.",
                )
                return
            patient, err, amb = await _resolve_patient_for_doctor(db, doctor, hint)
            if amb is not None:
                await _send_ambiguous_patient_buttons(
                    db,
                    doctor,
                    chat_id,
                    user_key,
                    amb,
                    back_state=_navigation_current_state(st0),
                )
                return
            if err or patient is None:
                await send_telegram_message(chat_id, err or MSG_NO_DATA)
                return
            await _send_patient_history_ui(
                db, doctor, chat_id, patient.id, user_key
            )
            return
        if intent in ("patient_show", "patient_edit"):
            hint = _patient_name_hint(text, entities)
            if not hint.strip():
                last_patient = await _last_active_patient(db, doctor, user_key)
                if last_patient is not None:
                    await _show_patient_card(
                        db, doctor, chat_id, user_key, last_patient
                    )
                    return
                await send_telegram_message(
                    chat_id,
                    "Indica el nombre o número del paciente.",
                )
                return
            patient, err, amb = await _resolve_patient_for_doctor(db, doctor, hint)
            if amb is not None:
                await _send_ambiguous_patient_buttons(
                    db,
                    doctor,
                    chat_id,
                    user_key,
                    amb,
                    back_state=_navigation_current_state(st0),
                )
                return
            if err or patient is None:
                await send_telegram_message(chat_id, err or MSG_NO_DATA)
                return
            await _show_patient_card(db, doctor, chat_id, user_key, patient)
            return
        if intent == "possible_mutation":
            await send_telegram_message(
                chat_id,
                "Las actualizaciones de peso, estatura, ciudad y archivo se realizan solo en el panel web.",
            )
            return
        if policy == "ambiguous_entity":
            await send_telegram_message(
                chat_id,
                "No estoy segura a qué te refieres. Usa el menú o da más contexto.",
                reply_markup=_menu_markup(),
            )
            return
        if policy == "needs_patient":
            await send_telegram_message(
                chat_id,
                "Necesito el nombre o número de paciente. "
                "Abre «Pacientes» o escribe por ejemplo: «historial de Maria».",
                reply_markup=_menu_markup(),
            )
            return
        await send_telegram_message(
            chat_id,
            "No interpreté ese mensaje de forma segura.\n"
            "Usa el menú para opciones guiadas.",
            reply_markup=_menu_markup(),
        )
        return

    if cmd in ("/ayuda", "/help"):
        await _send_help_screen(db, doctor, chat_id, user_key)
    elif cmd == "/menu":
        await _send_home_screen(
            db,
            doctor,
            chat_id,
            user_key,
            prefix="Menú principal:",
        )
    elif cmd == "/pacientes":
        await _send_patients_page(db, doctor, chat_id, user_key, page=1)
    elif cmd in ("/ficha", "/buscar"):
        if cmd == "/buscar" and not rest.strip():
            await _save_state(
                db,
                doctor.id,
                user_key,
                {"awaiting": "search_query"},
            )
            await send_telegram_message(
                chat_id,
                "Escribe nombre o apellido para buscar.",
                reply_markup=_cancel_markup(),
            )
        elif not rest.strip():
            await send_telegram_message(
                chat_id,
                "Toca «Pacientes» en el menú y elige un nombre, o usa «Buscar» para filtrar.",
                reply_markup=_menu_markup(),
            )
        else:
            patient, err, amb = await _resolve_patient_for_doctor(db, doctor, rest)
            if amb is not None:
                current_state = await _load_state(db, doctor.id, user_key)
                await _send_ambiguous_patient_buttons(
                    db,
                    doctor,
                    chat_id,
                    user_key,
                    amb,
                    back_state=_navigation_current_state(current_state),
                )
            elif err:
                await send_telegram_message(chat_id, err[:4090])
            elif patient:
                await _show_patient_card(db, doctor, chat_id, user_key, patient)
    elif cmd in ("/dieta", "/generardieta"):
        await send_telegram_message(
            chat_id,
            MSG_NO_DIETA_CMD,
            reply_markup=_menu_markup(),
        )
    elif cmd == "/pdf":
        await send_telegram_message(
            chat_id,
            MSG_NO_PDF_CMD,
            reply_markup=_menu_markup(),
        )
    else:
        await send_telegram_message(
            chat_id,
            "No reconozco ese comando. Usa el menú guiado para continuar.",
            reply_markup=_menu_markup(),
        )
