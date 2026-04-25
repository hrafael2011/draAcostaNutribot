from __future__ import annotations

import logging
from typing import Any

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


def _bot_url(method: str) -> str | None:
    token = settings.TELEGRAM_BOT_TOKEN
    if not token:
        return None
    return f"https://api.telegram.org/bot{token}/{method}"


def _telegram_ok(resp: httpx.Response) -> tuple[bool, dict[str, Any]]:
    try:
        body: dict[str, Any] = resp.json()
    except Exception:
        return False, {"parse_error": True, "status": resp.status_code}
    ok = bool(body.get("ok")) if "ok" in body else resp.is_success
    return ok, body


def _log_telegram_failure(
    method: str,
    *,
    status_code: int | None,
    body: dict[str, Any],
) -> None:
    logger.error(
        "Telegram API %s failed: status=%s description=%s error_code=%s body=%s",
        method,
        status_code,
        body.get("description"),
        body.get("error_code"),
        body,
    )


async def send_telegram_message(
    chat_id: str,
    text: str,
    *,
    reply_markup: dict[str, Any] | None = None,
) -> int | None:
    """Envía mensaje. Devuelve message_id de Telegram si la API respondió ok."""
    url = _bot_url("sendMessage")
    if not url:
        logger.warning("Telegram sendMessage skipped: TELEGRAM_BOT_TOKEN not set")
        return None
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            payload: dict[str, Any] = {
                "chat_id": chat_id,
                "text": text[:4090],
                "disable_web_page_preview": True,
            }
            if reply_markup:
                payload["reply_markup"] = reply_markup
            resp = await client.post(url, json=payload)
        ok, body = _telegram_ok(resp)
        if not ok or resp.status_code >= 400:
            _log_telegram_failure(
                "sendMessage", status_code=resp.status_code, body=body
            )
            return None
        result = body.get("result")
        if isinstance(result, dict):
            mid = result.get("message_id")
            if isinstance(mid, int):
                return mid
        return None
    except httpx.HTTPError as e:
        logger.error("Telegram sendMessage HTTP error: %s", e)
        return None


async def edit_telegram_message_reply_markup(
    chat_id: str,
    message_id: int,
    *,
    reply_markup: dict[str, Any] | None = None,
) -> None:
    """Quita o sustituye el teclado inline de un mensaje (reply_markup=None → teclado vacío)."""
    url = _bot_url("editMessageReplyMarkup")
    if not url:
        return
    markup = (
        reply_markup
        if reply_markup is not None
        else {"inline_keyboard": []}
    )
    payload: dict[str, Any] = {
        "chat_id": chat_id,
        "message_id": message_id,
        "reply_markup": markup,
    }
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(url, json=payload)
        ok, body = _telegram_ok(resp)
        if not ok or resp.status_code >= 400:
            _log_telegram_failure(
                "editMessageReplyMarkup", status_code=resp.status_code, body=body
            )
    except httpx.HTTPError as e:
        logger.error("Telegram editMessageReplyMarkup HTTP error: %s", e)


async def send_telegram_document(
    chat_id: str,
    content: bytes,
    filename: str,
    *,
    caption: str | None = None,
) -> None:
    url = _bot_url("sendDocument")
    if not url:
        logger.warning("Telegram sendDocument skipped: TELEGRAM_BOT_TOKEN not set")
        return
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                url,
                data={
                    "chat_id": chat_id,
                    "caption": (caption or "")[:1024],
                },
                files={
                    "document": (
                        filename,
                        content,
                        "application/pdf",
                    )
                },
            )
        ok, body = _telegram_ok(resp)
        if not ok or resp.status_code >= 400:
            _log_telegram_failure(
                "sendDocument", status_code=resp.status_code, body=body
            )
    except httpx.HTTPError as e:
        logger.error("Telegram sendDocument HTTP error: %s", e)


async def answer_telegram_callback_query(
    callback_query_id: str,
    *,
    text: str | None = None,
    show_alert: bool = False,
) -> None:
    url = _bot_url("answerCallbackQuery")
    if not url:
        logger.warning(
            "Telegram answerCallbackQuery skipped: TELEGRAM_BOT_TOKEN not set"
        )
        return
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            payload: dict[str, Any] = {
                "callback_query_id": callback_query_id,
                "show_alert": show_alert,
            }
            if text:
                payload["text"] = text[:180]
            resp = await client.post(url, json=payload)
        ok, body = _telegram_ok(resp)
        if not ok or resp.status_code >= 400:
            _log_telegram_failure(
                "answerCallbackQuery", status_code=resp.status_code, body=body
            )
    except httpx.HTTPError as e:
        logger.error("Telegram answerCallbackQuery HTTP error: %s", e)
