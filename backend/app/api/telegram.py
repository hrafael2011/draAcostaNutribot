import logging
import secrets
from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_doctor
from app.core.config import settings
from app.core.database import get_db
from app.models import (
    AuditLog,
    Doctor,
    DoctorTelegramBinding,
    TelegramPendingLink,
    TelegramProcessedUpdate,
    utcnow,
)
from app.schemas import TelegramBindStartOut, TelegramBindingOut
from app.services.telegram_handler import handle_telegram_update

logger = logging.getLogger(__name__)
router = APIRouter()
PERMANENT_LINK_DAYS = 36500


def _parse_update_id(body: Any) -> int | None:
    if not isinstance(body, dict):
        return None
    raw = body.get("update_id")
    if isinstance(raw, int):
        return raw
    if isinstance(raw, str) and raw.isdigit():
        return int(raw)
    return None


@router.get("/binding", response_model=TelegramBindingOut)
async def get_binding(
    db: AsyncSession = Depends(get_db),
    doctor: Doctor = Depends(get_current_doctor),
):
    result = await db.execute(
        select(DoctorTelegramBinding)
        .where(
            DoctorTelegramBinding.doctor_id == doctor.id,
            DoctorTelegramBinding.is_active.is_(True),
        )
        .order_by(DoctorTelegramBinding.id.desc())
        .limit(1)
    )
    binding = result.scalar_one_or_none()
    linked = binding is not None
    return TelegramBindingOut(
        linked=linked,
        telegram_user_id=(
            binding.telegram_user_id if binding else doctor.telegram_user_id
        ),
        telegram_username=(
            binding.telegram_username if binding else doctor.telegram_username
        ),
        bot_username=(
            settings.TELEGRAM_BOT_USERNAME.strip().lstrip("@")
            if settings.TELEGRAM_BOT_USERNAME
            else None
        ),
    )


@router.post("/binding/start", response_model=TelegramBindStartOut)
async def start_binding(
    db: AsyncSession = Depends(get_db),
    doctor: Doctor = Depends(get_current_doctor),
):
    if not settings.TELEGRAM_BOT_TOKEN or not settings.TELEGRAM_BOT_USERNAME:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Telegram bot is not configured (TELEGRAM_BOT_TOKEN / TELEGRAM_BOT_USERNAME).",
        )
    pending_result = await db.execute(
        select(TelegramPendingLink).where(TelegramPendingLink.doctor_id == doctor.id)
    )
    pending = pending_result.scalar_one_or_none()
    expires_at = utcnow() + timedelta(days=PERMANENT_LINK_DAYS)
    if pending is None:
        pending = TelegramPendingLink(
            doctor_id=doctor.id,
            code=secrets.token_hex(8),
            expires_at=expires_at,
        )
        db.add(pending)
    else:
        pending.expires_at = expires_at
    await db.commit()
    username = settings.TELEGRAM_BOT_USERNAME.strip().lstrip("@")
    deep_link = f"https://t.me/{username}?start={pending.code}"
    return TelegramBindStartOut(
        deep_link=deep_link,
        code=pending.code,
        expires_at=expires_at,
    )


@router.post("/binding/reset", response_model=TelegramBindingOut)
async def reset_binding(
    db: AsyncSession = Depends(get_db),
    doctor: Doctor = Depends(get_current_doctor),
):
    await db.execute(
        delete(DoctorTelegramBinding).where(
            DoctorTelegramBinding.doctor_id == doctor.id
        )
    )
    # No borrar TelegramPendingLink: así el mismo deep link (t.me/...?start=CODIGO)
    # sigue válido tras desvincular, útil en pruebas y evita "enlace inválido" al reutilizar.
    pending_refresh = await db.execute(
        select(TelegramPendingLink).where(TelegramPendingLink.doctor_id == doctor.id)
    )
    pending_row = pending_refresh.scalar_one_or_none()
    if pending_row:
        pending_row.expires_at = utcnow() + timedelta(days=PERMANENT_LINK_DAYS)
    doctor.telegram_user_id = None
    doctor.telegram_username = None
    doctor.updated_at = utcnow()
    db.add(
        AuditLog(
            doctor_id=doctor.id,
            action="telegram_unbind",
            entity_type="doctor",
            entity_id=doctor.id,
            payload_json=None,
        )
    )
    await db.commit()
    return TelegramBindingOut(
        linked=False,
        telegram_user_id=None,
        telegram_username=None,
        bot_username=(
            settings.TELEGRAM_BOT_USERNAME.strip().lstrip("@")
            if settings.TELEGRAM_BOT_USERNAME
            else None
        ),
    )


@router.post("/webhook")
async def telegram_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    expected = settings.TELEGRAM_WEBHOOK_SECRET
    if expected:
        got = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
        if got != expected:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    try:
        body = await request.json()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON",
        ) from exc

    update_id = _parse_update_id(body)
    if update_id is not None:
        try:
            db.add(TelegramProcessedUpdate(update_id=update_id))
            await db.flush()
        except IntegrityError:
            await db.rollback()
            return {"ok": True}

    try:
        await handle_telegram_update(db, body)
        await db.commit()
    except Exception:
        await db.rollback()
        logger.exception("telegram webhook handler failed")
        return {"ok": True}

    return {"ok": True}
