"""Comportamiento del cliente HTTP hacia Telegram (sin red real)."""

import asyncio
import logging
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services import telegram_client


def test_send_message_logs_error_when_telegram_returns_ok_false(caplog: pytest.LogCaptureFixture) -> None:
    """Evidencia en CI: no silenciar fallos con HTTP 200 y ok:false."""
    caplog.set_level(logging.ERROR, logger="app.services.telegram_client")

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "ok": False,
        "description": "Bad Request: chat not found",
        "error_code": 400,
    }

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_resp)

    async def _run() -> None:
        with patch.object(telegram_client.settings, "TELEGRAM_BOT_TOKEN", "123456:FAKE"):
            with patch("httpx.AsyncClient") as Client:
                Client.return_value.__aenter__.return_value = mock_client
                await telegram_client.send_telegram_message("999", "hola")

    asyncio.run(_run())

    assert any(
        "Telegram API sendMessage failed" in r.message for r in caplog.records
    ), caplog.text


def test_send_message_skipped_logs_warning_without_token(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.WARNING, logger="app.services.telegram_client")

    async def _run() -> None:
        with patch.object(telegram_client.settings, "TELEGRAM_BOT_TOKEN", ""):
            await telegram_client.send_telegram_message("999", "hola")

    asyncio.run(_run())

    assert any("skipped" in r.message.lower() for r in caplog.records), caplog.text
