"""
E2E ligero contra la app en proceso (sin servidor TCP).
Requiere PostgreSQL accesible con DATABASE_URL y migraciones aplicadas.
"""
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

BACKEND_ROOT = Path(__file__).resolve().parents[1]

# Cargar .env del backend si existe
try:
    from dotenv import load_dotenv

    load_dotenv(BACKEND_ROOT / ".env")
except ImportError:
    pass

from app.demo_seed import DEMO_DOCTOR_EMAIL, DEMO_DOCTOR_PASSWORD
from app.main import app


def _skip_if_no_db_output(msg: str) -> None:
    err = msg.lower()
    if "connection refused" in err or "name or service not known" in err:
        pytest.skip(f"Base de datos no alcanzable:\n{msg}")
    if "password authentication failed" in err:
        pytest.skip(f"Base de datos — credenciales:\n{msg}")


@pytest.fixture(scope="module")
def seeded():
    # Subproceso: no mezclar el loop de asyncio.run(seed) con TestClient + asyncpg.
    p = subprocess.run(
        [sys.executable, str(BACKEND_ROOT / "scripts" / "seed_demo.py")],
        cwd=str(BACKEND_ROOT),
        env={**os.environ},
        capture_output=True,
        text=True,
        timeout=120,
    )
    out = (p.stdout or "") + (p.stderr or "")
    if p.returncode != 0:
        _skip_if_no_db_output(out)
        pytest.fail(f"seed_demo falló:\n{out}")


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@pytest.mark.usefixtures("seeded")
def test_health(client: TestClient):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json().get("status") == "ok"


@pytest.mark.usefixtures("seeded")
def test_login_demo_doctor(client: TestClient):
    r = client.post(
        "/api/auth/token",
        data={
            "username": DEMO_DOCTOR_EMAIL,
            "password": DEMO_DOCTOR_PASSWORD,
        },
    )
    if r.status_code != 200:
        pytest.fail(f"login {r.status_code}: {r.text}")
    data = r.json()
    assert "access_token" in data


@pytest.mark.usefixtures("seeded")
def test_patients_and_summary(client: TestClient):
    tr = client.post(
        "/api/auth/token",
        data={
            "username": DEMO_DOCTOR_EMAIL,
            "password": DEMO_DOCTOR_PASSWORD,
        },
    )
    assert tr.status_code == 200, tr.text
    token = tr.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    r = client.get("/api/patients?page_size=50", headers=headers)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["total"] >= 2
    names = {f"{p['first_name']} {p['last_name']}" for p in body["items"]}
    assert "Maria Lopez" in names
    assert "Carlos Ruiz" in names

    maria = next(
        p for p in body["items"] if p["first_name"] == "Maria" and p["last_name"] == "Lopez"
    )
    sid = client.get(f"/api/patients/{maria['id']}/summary", headers=headers)
    assert sid.status_code == 200, sid.text
    assert sid.json()["profile_flags"]["is_profile_complete"] is True


@pytest.mark.usefixtures("seeded")
def test_diet_generate_requires_openai_or_succeeds(client: TestClient):
    tr = client.post(
        "/api/auth/token",
        data={
            "username": DEMO_DOCTOR_EMAIL,
            "password": DEMO_DOCTOR_PASSWORD,
        },
    )
    assert tr.status_code == 200
    token = tr.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    pr = client.get("/api/patients?page_size=50", headers=headers)
    maria = next(
        p
        for p in pr.json()["items"]
        if p["first_name"] == "Maria" and p["last_name"] == "Lopez"
    )

    r = client.post(
        "/api/diets/generate",
        headers=headers,
        json={
            "patient_id": maria["id"],
            "doctor_instruction": "Demo E2E — comidas sencillas RD",
        },
    )
    if os.getenv("OPENAI_API_KEY"):
        assert r.status_code == 201, r.text
        assert r.json().get("patient_id") == maria["id"]
    else:
        assert r.status_code == 503
        detail = r.json().get("detail", {})
        assert detail.get("code") == "openai_config"


@pytest.mark.usefixtures("seeded")
def test_telegram_webhook_accepts_update(client: TestClient):
    r = client.post("/api/telegram/webhook", json={"update_id": 1})
    assert r.status_code == 200
    assert r.json().get("ok") is True


@pytest.mark.usefixtures("seeded")
def test_telegram_binding_start_same_code_twice(client: TestClient):
    tr = client.post(
        "/api/auth/token",
        data={
            "username": DEMO_DOCTOR_EMAIL,
            "password": DEMO_DOCTOR_PASSWORD,
        },
    )
    assert tr.status_code == 200, tr.text
    headers = {"Authorization": f"Bearer {tr.json()['access_token']}"}
    client.post("/api/telegram/binding/reset", headers=headers)
    r1 = client.post("/api/telegram/binding/start", headers=headers)
    if r1.status_code == 503:
        pytest.skip("Telegram bot not configured for binding test")
    assert r1.status_code == 200, r1.text
    j1 = r1.json()
    r2 = client.post("/api/telegram/binding/start", headers=headers)
    assert r2.status_code == 200, r2.text
    j2 = r2.json()
    assert j1["code"] == j2["code"]
    assert j1["deep_link"] == j2["deep_link"]


@pytest.mark.usefixtures("seeded")
def test_telegram_dieta_and_pdf_commands_disabled(client: TestClient, monkeypatch):
    sent_messages: list[dict] = []

    async def fake_send_message(chat_id: str, text: str, **kwargs) -> None:
        sent_messages.append({"chat_id": chat_id, "text": text, "kwargs": kwargs})

    async def fake_send_document(*args, **kwargs) -> None:
        pytest.fail("No se debe enviar documento con /dieta ni /pdf")

    from app.services import telegram_handler

    monkeypatch.setattr(telegram_handler, "send_telegram_message", fake_send_message)
    monkeypatch.setattr(telegram_handler, "send_telegram_document", fake_send_document)

    tr = client.post(
        "/api/auth/token",
        data={
            "username": DEMO_DOCTOR_EMAIL,
            "password": DEMO_DOCTOR_PASSWORD,
        },
    )
    assert tr.status_code == 200, tr.text
    token = tr.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    client.post("/api/telegram/binding/reset", headers=headers)
    bind = client.post("/api/telegram/binding/start", headers=headers)
    assert bind.status_code == 200, bind.text
    code = bind.json()["code"]

    client.post(
        "/api/telegram/webhook",
        json={
            "update_id": 2001,
            "message": {
                "message_id": 10,
                "chat": {"id": 777001, "type": "private"},
                "from": {"id": 999001, "username": "demo_doc"},
                "text": f"/start {code}",
            },
        },
    )

    client.post(
        "/api/telegram/webhook",
        json={
            "update_id": 2002,
            "message": {
                "message_id": 11,
                "chat": {"id": 777001, "type": "private"},
                "from": {"id": 999001, "username": "demo_doc"},
                "text": "/dieta@AcostaDiet_bot Maria genera una dieta de 7 dias",
            },
        },
    )
    assert any(
        "menú" in m["text"].lower() and "genera una dieta" in m["text"].lower()
        for m in sent_messages
    ), "Debe orientar a menú o lenguaje natural, sin ejecutar /dieta"
    assert not any("Confirmar generación" in m["text"] for m in sent_messages)

    n = len(sent_messages)
    client.post(
        "/api/telegram/webhook",
        json={
            "update_id": 2003,
            "message": {
                "message_id": 12,
                "chat": {"id": 777001, "type": "private"},
                "from": {"id": 999001, "username": "demo_doc"},
                "text": "/pdf 999",
            },
        },
    )
    new_msgs = sent_messages[n:]
    assert any("historial" in m["text"].lower() for m in new_msgs), "Debe orientar al historial, sin /pdf"
    assert any(
        m["kwargs"].get("reply_markup", {}).get("inline_keyboard")
        for m in new_msgs
    )


@pytest.mark.usefixtures("seeded")
def test_telegram_menu_callback_and_weight_update(client: TestClient, monkeypatch):
    sent_messages: list[dict] = []

    async def fake_send_message(chat_id: str, text: str, **kwargs) -> None:
        sent_messages.append({"chat_id": chat_id, "text": text, "kwargs": kwargs})

    async def fake_send_document(*args, **kwargs) -> None:
        return

    async def fake_answer_callback(*args, **kwargs) -> None:
        return

    from app.services import telegram_handler

    monkeypatch.setattr(telegram_handler, "send_telegram_message", fake_send_message)
    monkeypatch.setattr(telegram_handler, "send_telegram_document", fake_send_document)
    monkeypatch.setattr(telegram_handler, "answer_telegram_callback_query", fake_answer_callback)

    tr = client.post(
        "/api/auth/token",
        data={
            "username": DEMO_DOCTOR_EMAIL,
            "password": DEMO_DOCTOR_PASSWORD,
        },
    )
    assert tr.status_code == 200, tr.text
    token = tr.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    lp = client.get("/api/patients?page_size=1", headers=headers)
    assert lp.status_code == 200, lp.text
    patient_id = lp.json()["items"][0]["id"]
    client.post("/api/telegram/binding/reset", headers=headers)
    bind = client.post("/api/telegram/binding/start", headers=headers)
    assert bind.status_code == 200, bind.text
    code = bind.json()["code"]

    chat_id = 777777
    user_id = 888888
    r_start = client.post(
        "/api/telegram/webhook",
        json={
            "update_id": 4001,
            "message": {
                "message_id": 41,
                "chat": {"id": chat_id, "type": "private"},
                "from": {"id": user_id, "username": "demo_doc"},
                "text": f"/start {code}",
            },
        },
    )
    assert r_start.status_code == 200, r_start.text

    r_cb = client.post(
        "/api/telegram/webhook",
        json={
            "update_id": 4002,
            "callback_query": {
                "id": "cb-1",
                "from": {"id": user_id, "username": "demo_doc"},
                "data": f"patient:weight:{patient_id}",
                "message": {"chat": {"id": chat_id, "type": "private"}},
            },
        },
    )
    assert r_cb.status_code == 200, r_cb.text

    r_weight = client.post(
        "/api/telegram/webhook",
        json={
            "update_id": 4003,
            "message": {
                "message_id": 43,
                "chat": {"id": chat_id, "type": "private"},
                "from": {"id": user_id, "username": "demo_doc"},
                "text": "71.4",
            },
        },
    )
    assert r_weight.status_code == 200, r_weight.text
    assert any("Confirmar peso" in m["text"] for m in sent_messages)
    r_confirm = client.post(
        "/api/telegram/webhook",
        json={
            "update_id": 4004,
            "callback_query": {
                "id": "cb-metric-1",
                "from": {"id": user_id, "username": "demo_doc"},
                "data": f"metric:confirm:{patient_id}:weight",
                "message": {"chat": {"id": chat_id, "type": "private"}},
            },
        },
    )
    assert r_confirm.status_code == 200, r_confirm.text
    assert any("asistente del consultorio" in m["text"].lower() for m in sent_messages)
    assert any("Peso guardado" in m["text"] for m in sent_messages)


@pytest.mark.usefixtures("seeded")
def test_telegram_guided_diet_flow_and_cancel(client: TestClient, monkeypatch):
    sent_messages: list[dict] = []
    sent_docs: list[dict] = []

    async def fake_send_message(chat_id: str, text: str, **kwargs) -> None:
        sent_messages.append({"chat_id": chat_id, "text": text, "kwargs": kwargs})

    async def fake_send_document(
        chat_id: str,
        content: bytes,
        filename: str,
        *,
        caption: str | None = None,
    ) -> None:
        sent_docs.append(
            {
                "chat_id": chat_id,
                "content": content,
                "filename": filename,
                "caption": caption,
            }
        )

    async def fake_answer_callback(*args, **kwargs) -> None:
        return

    from app.services import telegram_handler

    monkeypatch.setattr(telegram_handler, "send_telegram_message", fake_send_message)
    monkeypatch.setattr(telegram_handler, "send_telegram_document", fake_send_document)
    monkeypatch.setattr(telegram_handler, "answer_telegram_callback_query", fake_answer_callback)

    tr = client.post(
        "/api/auth/token",
        data={
            "username": DEMO_DOCTOR_EMAIL,
            "password": DEMO_DOCTOR_PASSWORD,
        },
    )
    assert tr.status_code == 200, tr.text
    token = tr.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    lp = client.get("/api/patients?page_size=50", headers=headers)
    assert lp.status_code == 200, lp.text
    patient = next(
        p
        for p in lp.json()["items"]
        if p["first_name"] == "Maria" and p["last_name"] == "Lopez"
    )
    patient_id = patient["id"]
    client.post("/api/telegram/binding/reset", headers=headers)
    bind = client.post("/api/telegram/binding/start", headers=headers)
    code = bind.json()["code"]

    chat_id = 779001
    user_id = 889001
    client.post(
        "/api/telegram/webhook",
        json={
            "update_id": 6001,
            "message": {
                "message_id": 61,
                "chat": {"id": chat_id, "type": "private"},
                "from": {"id": user_id, "username": "demo_doc"},
                "text": f"/start {code}",
            },
        },
    )
    client.post(
        "/api/telegram/webhook",
        json={
            "update_id": 6002,
            "callback_query": {
                "id": "cb-diet-1",
                "from": {"id": user_id, "username": "demo_doc"},
                "data": f"patient:diet:{patient_id}",
                "message": {"chat": {"id": chat_id, "type": "private"}},
            },
        },
    )
    client.post(
        "/api/telegram/webhook",
        json={
            "update_id": 6003,
            "message": {
                "message_id": 62,
                "chat": {"id": chat_id, "type": "private"},
                "from": {"id": user_id, "username": "demo_doc"},
                "text": "sin mariscos y mas proteina",
            },
        },
    )
    client.post(
        "/api/telegram/webhook",
        json={
            "update_id": 6004,
            "callback_query": {
                "id": "cb-diet-2",
                "from": {"id": user_id, "username": "demo_doc"},
                "data": f"diet:cancel:{patient_id}",
                "message": {"chat": {"id": chat_id, "type": "private"}},
            },
        },
    )

    assert any("especificaciones extra" in m["text"].lower() for m in sent_messages)
    assert any("múltiplo de 7" in m["text"].lower() for m in sent_messages)
    assert any("Flujo cancelado" in m["text"] for m in sent_messages)
    assert not sent_docs

    sent_messages.clear()
    sent_docs.clear()
    client.post(
        "/api/telegram/webhook",
        json={
            "update_id": 6005,
            "callback_query": {
                "id": "cb-diet-3",
                "from": {"id": user_id, "username": "demo_doc"},
                "data": f"patient:diet:{patient_id}",
                "message": {"chat": {"id": chat_id, "type": "private"}},
            },
        },
    )
    client.post(
        "/api/telegram/webhook",
        json={
            "update_id": 6006,
            "message": {
                "message_id": 63,
                "chat": {"id": chat_id, "type": "private"},
                "from": {"id": user_id, "username": "demo_doc"},
                "text": "saltar",
            },
        },
    )
    client.post(
        "/api/telegram/webhook",
        json={
            "update_id": 60061,
            "message": {
                "message_id": 64,
                "chat": {"id": chat_id, "type": "private"},
                "from": {"id": user_id, "username": "demo_doc"},
                "text": "7",
            },
        },
    )
    client.post(
        "/api/telegram/webhook",
        json={
            "update_id": 60062,
            "callback_query": {
                "id": "cb-diet-35",
                "from": {"id": user_id, "username": "demo_doc"},
                "data": f"diet:meals:4:{patient_id}",
                "message": {"chat": {"id": chat_id, "type": "private"}},
            },
        },
    )
    client.post(
        "/api/telegram/webhook",
        json={
            "update_id": 60063,
            "callback_query": {
                "id": "cb-diet-36",
                "from": {"id": user_id, "username": "demo_doc"},
                "data": f"diet:smd:a:{patient_id}",
                "message": {"chat": {"id": chat_id, "type": "private"}},
            },
        },
    )
    client.post(
        "/api/telegram/webhook",
        json={
            "update_id": 6007,
            "callback_query": {
                "id": "cb-diet-4",
                "from": {"id": user_id, "username": "demo_doc"},
                "data": f"diet:confirm:{patient_id}",
                "message": {"chat": {"id": chat_id, "type": "private"}},
            },
        },
    )
    if os.getenv("OPENAI_API_KEY"):
        preview_msgs = [
            m
            for m in sent_messages
            if "Vista previa" in m["text"]
            and "pendiente de aprobación" in m["text"].lower()
        ]
        assert preview_msgs, [m["text"][:200] for m in sent_messages]
        m_id = re.search(r"Dieta\s*#(\d+)", preview_msgs[0]["text"])
        assert m_id, preview_msgs[0]["text"]
        diet_id_preview = int(m_id.group(1))
        client.post(
            "/api/telegram/webhook",
            json={
                "update_id": 6008,
                "callback_query": {
                    "id": "cb-diet-5",
                    "from": {"id": user_id, "username": "demo_doc"},
                    "data": f"diet:preview:approve:{diet_id_preview}",
                    "message": {"chat": {"id": chat_id, "type": "private"}},
                },
            },
        )
        assert any("aprobada" in m["text"].lower() for m in sent_messages)
        assert sent_docs


@pytest.mark.usefixtures("seeded")
def test_telegram_history_with_pdf_button(client: TestClient, monkeypatch):
    sent_messages: list[dict] = []
    sent_docs: list[dict] = []

    async def fake_send_message(chat_id: str, text: str, **kwargs) -> None:
        sent_messages.append({"chat_id": chat_id, "text": text, "kwargs": kwargs})

    async def fake_send_document(
        chat_id: str,
        content: bytes,
        filename: str,
        *,
        caption: str | None = None,
    ) -> None:
        sent_docs.append(
            {
                "chat_id": chat_id,
                "content": content,
                "filename": filename,
                "caption": caption,
            }
        )

    async def fake_answer_callback(*args, **kwargs) -> None:
        return

    from app.services import telegram_handler

    monkeypatch.setattr(telegram_handler, "send_telegram_message", fake_send_message)
    monkeypatch.setattr(telegram_handler, "send_telegram_document", fake_send_document)
    monkeypatch.setattr(telegram_handler, "answer_telegram_callback_query", fake_answer_callback)

    tr = client.post(
        "/api/auth/token",
        data={
            "username": DEMO_DOCTOR_EMAIL,
            "password": DEMO_DOCTOR_PASSWORD,
        },
    )
    token = tr.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    pr = client.get("/api/patients?page_size=50", headers=headers)
    maria = next(
        p
        for p in pr.json()["items"]
        if p["first_name"] == "Maria" and p["last_name"] == "Lopez"
    )
    diet_gen = client.post(
        "/api/diets/generate",
        headers=headers,
        json={"patient_id": maria["id"], "doctor_instruction": "e2e history"},
    )
    if not os.getenv("OPENAI_API_KEY") and diet_gen.status_code != 201:
        diets_r = client.get(
            "/api/diets",
            headers=headers,
            params={"patient_id": maria["id"], "page_size": 1},
        )
        items = diets_r.json().get("items") or []
        if not items:
            pytest.skip("Sin dietas para validar historial/pdf por botón")
        diet_id = items[0]["id"]
    else:
        assert diet_gen.status_code == 201, diet_gen.text
        diet_id = diet_gen.json()["id"]

    client.post("/api/telegram/binding/reset", headers=headers)
    bind = client.post("/api/telegram/binding/start", headers=headers)
    code = bind.json()["code"]
    chat_id = 779111
    user_id = 889111
    client.post(
        "/api/telegram/webhook",
        json={
            "update_id": 6101,
            "message": {
                "message_id": 71,
                "chat": {"id": chat_id, "type": "private"},
                "from": {"id": user_id, "username": "demo_doc"},
                "text": f"/start {code}",
            },
        },
    )
    client.post(
        "/api/telegram/webhook",
        json={
            "update_id": 6102,
            "callback_query": {
                "id": "cb-h1",
                "from": {"id": user_id, "username": "demo_doc"},
                "data": f"patient:history:{maria['id']}:1",
                "message": {"chat": {"id": chat_id, "type": "private"}},
            },
        },
    )
    history_message = next(
        (m for m in sent_messages if "Historial de dietas" in m["text"]),
        None,
    )
    assert history_message is not None
    keyboard = history_message["kwargs"].get("reply_markup", {}).get("inline_keyboard", [])
    pdf_callbacks = [b["callback_data"] for row in keyboard for b in row if "callback_data" in b]
    assert any(cb.startswith("diet:pdf:") for cb in pdf_callbacks)

    client.post(
        "/api/telegram/webhook",
        json={
            "update_id": 6103,
            "callback_query": {
                "id": "cb-h2",
                "from": {"id": user_id, "username": "demo_doc"},
                "data": f"diet:pdf:{diet_id}",
                "message": {"chat": {"id": chat_id, "type": "private"}},
            },
        },
    )
    assert sent_docs
    assert sent_docs[-1]["content"][:4] == b"%PDF"


@pytest.mark.usefixtures("seeded")
def test_telegram_free_text_safe_intent_patients(client: TestClient, monkeypatch):
    sent_messages: list[dict] = []

    async def fake_send_message(chat_id: str, text: str, **kwargs) -> None:
        sent_messages.append({"chat_id": chat_id, "text": text, "kwargs": kwargs})

    async def fake_send_document(*args, **kwargs) -> None:
        return

    from app.services import telegram_handler

    monkeypatch.setattr(telegram_handler, "send_telegram_message", fake_send_message)
    monkeypatch.setattr(telegram_handler, "send_telegram_document", fake_send_document)

    tr = client.post(
        "/api/auth/token",
        data={
            "username": DEMO_DOCTOR_EMAIL,
            "password": DEMO_DOCTOR_PASSWORD,
        },
    )
    assert tr.status_code == 200, tr.text
    token = tr.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    client.post("/api/telegram/binding/reset", headers=headers)
    bind = client.post("/api/telegram/binding/start", headers=headers)
    assert bind.status_code == 200, bind.text
    code = bind.json()["code"]

    chat_id = 776001
    user_id = 995001
    r_start = client.post(
        "/api/telegram/webhook",
        json={
            "update_id": 5001,
            "message": {
                "message_id": 51,
                "chat": {"id": chat_id, "type": "private"},
                "from": {"id": user_id, "username": "demo_doc"},
                "text": f"/start {code}",
            },
        },
    )
    assert r_start.status_code == 200, r_start.text

    r_text = client.post(
        "/api/telegram/webhook",
        json={
            "update_id": 5002,
            "message": {
                "message_id": 52,
                "chat": {"id": chat_id, "type": "private"},
                "from": {"id": user_id, "username": "demo_doc"},
                "text": "quiero ver mis pacientes",
            },
        },
    )
    assert r_text.status_code == 200, r_text.text
    assert any("Selecciona un paciente" in m["text"] for m in sent_messages)


@pytest.mark.usefixtures("seeded")
def test_telegram_nl_diet_stats_and_lb_weight_confirm(client: TestClient, monkeypatch):
    sent_messages: list[dict] = []

    async def fake_send_message(chat_id: str, text: str, **kwargs) -> None:
        sent_messages.append({"chat_id": chat_id, "text": text, "kwargs": kwargs})

    async def fake_send_document(*args, **kwargs) -> None:
        return

    async def fake_answer_callback(*args, **kwargs) -> None:
        return

    from app.services import telegram_handler

    monkeypatch.setattr(telegram_handler, "send_telegram_message", fake_send_message)
    monkeypatch.setattr(telegram_handler, "send_telegram_document", fake_send_document)
    monkeypatch.setattr(telegram_handler, "answer_telegram_callback_query", fake_answer_callback)

    tr = client.post(
        "/api/auth/token",
        data={
            "username": DEMO_DOCTOR_EMAIL,
            "password": DEMO_DOCTOR_PASSWORD,
        },
    )
    assert tr.status_code == 200, tr.text
    token = tr.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    lp = client.get("/api/patients?page_size=1", headers=headers)
    patient_id = lp.json()["items"][0]["id"]
    client.post("/api/telegram/binding/reset", headers=headers)
    bind = client.post("/api/telegram/binding/start", headers=headers)
    code = bind.json()["code"]
    chat_id = 776501
    user_id = 995501
    client.post(
        "/api/telegram/webhook",
        json={
            "update_id": 5201,
            "message": {
                "message_id": 81,
                "chat": {"id": chat_id, "type": "private"},
                "from": {"id": user_id, "username": "demo_doc"},
                "text": f"/start {code}",
            },
        },
    )
    client.post(
        "/api/telegram/webhook",
        json={
            "update_id": 5202,
            "message": {
                "message_id": 82,
                "chat": {"id": chat_id, "type": "private"},
                "from": {"id": user_id, "username": "demo_doc"},
                "text": "cuántas dietas he generado",
            },
        },
    )
    assert any("dietas generadas" in m["text"].lower() for m in sent_messages)
    sent_messages.clear()
    client.post(
        "/api/telegram/webhook",
        json={
            "update_id": 5203,
            "callback_query": {
                "id": "cb-w2",
                "from": {"id": user_id, "username": "demo_doc"},
                "data": f"patient:weight:{patient_id}",
                "message": {"chat": {"id": chat_id, "type": "private"}},
            },
        },
    )
    client.post(
        "/api/telegram/webhook",
        json={
            "update_id": 5204,
            "message": {
                "message_id": 83,
                "chat": {"id": chat_id, "type": "private"},
                "from": {"id": user_id, "username": "demo_doc"},
                "text": "154 lb",
            },
        },
    )
    assert any("Confirmar peso" in m["text"] and "69.85" in m["text"] for m in sent_messages)
    client.post(
        "/api/telegram/webhook",
        json={
            "update_id": 5205,
            "callback_query": {
                "id": "cb-w3",
                "from": {"id": user_id, "username": "demo_doc"},
                "data": f"metric:confirm:{patient_id}:weight",
                "message": {"chat": {"id": chat_id, "type": "private"}},
            },
        },
    )
    assert any("Peso guardado" in m["text"] for m in sent_messages)


@pytest.mark.usefixtures("seeded")
def test_telegram_natural_language_starts_guided_diet(client: TestClient, monkeypatch):
    sent_messages: list[dict] = []

    async def fake_send_message(chat_id: str, text: str, **kwargs) -> None:
        sent_messages.append({"chat_id": chat_id, "text": text, "kwargs": kwargs})

    async def fake_send_document(*args, **kwargs) -> None:
        return

    from app.services import telegram_handler

    monkeypatch.setattr(telegram_handler, "send_telegram_message", fake_send_message)
    monkeypatch.setattr(telegram_handler, "send_telegram_document", fake_send_document)

    tr = client.post(
        "/api/auth/token",
        data={
            "username": DEMO_DOCTOR_EMAIL,
            "password": DEMO_DOCTOR_PASSWORD,
        },
    )
    assert tr.status_code == 200, tr.text
    token = tr.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    client.post("/api/telegram/binding/reset", headers=headers)
    bind = client.post("/api/telegram/binding/start", headers=headers)
    code = bind.json()["code"]

    chat_id = 776101
    user_id = 995101
    client.post(
        "/api/telegram/webhook",
        json={
            "update_id": 5101,
            "message": {
                "message_id": 53,
                "chat": {"id": chat_id, "type": "private"},
                "from": {"id": user_id, "username": "demo_doc"},
                "text": f"/start {code}",
            },
        },
    )

    r_text = client.post(
        "/api/telegram/webhook",
        json={
            "update_id": 5102,
            "message": {
                "message_id": 54,
                "chat": {"id": chat_id, "type": "private"},
                "from": {"id": user_id, "username": "demo_doc"},
                "text": "genera una dieta para Maria",
            },
        },
    )
    assert r_text.status_code == 200, r_text.text
    assert any("especificaciones extra" in m["text"].lower() for m in sent_messages)


@pytest.mark.usefixtures("seeded")
def test_telegram_natural_language_manual_flow_reaches_preview_and_approval(
    client: TestClient, monkeypatch
):
    sent_messages: list[dict] = []
    sent_pdf: list[int] = []
    create_calls: list[dict] = []

    async def fake_send_message(chat_id: str, text: str, **kwargs) -> None:
        sent_messages.append({"chat_id": chat_id, "text": text, "kwargs": kwargs})

    async def fake_send_document(*args, **kwargs) -> None:
        return

    async def fake_answer_callback(*args, **kwargs) -> None:
        return

    async def fake_send_diet_pdf(db, doctor, chat_id, diet, *, patient=None) -> None:
        sent_pdf.append(diet.id)

    from app.models import Diet
    from app.services import telegram_handler
    from app.services.plan_meals import meal_slots_for_count

    async def fake_create_new_diet(
        db, doctor, patient_id, instruction, *, diet_status="generated", **kwargs
    ):
        create_calls.append(dict(kwargs))
        meals_per_day = kwargs.get("meals_per_day", 4)
        meal_slots = meal_slots_for_count(meals_per_day)
        diet = Diet(
            patient_id=patient_id,
            doctor_id=doctor.id,
            status=diet_status,
            title="Plan NL",
            summary="Generado desde NL",
            structured_plan_json={
                "title": "Plan NL",
                "summary": "Generado desde NL",
                "daily_calories": kwargs.get("manual_targets", {}).get(
                    "daily_calories", 1800
                ),
                "meals_per_day": meals_per_day,
                "meal_slots": meal_slots,
                "days": [
                    {
                        "day": 1,
                        "meals": {slot: f"Meal {slot}" for slot in meal_slots},
                    }
                ],
            },
            notes=instruction,
        )
        db.add(diet)
        await db.flush()
        await db.refresh(diet)
        return diet

    monkeypatch.setattr(telegram_handler, "send_telegram_message", fake_send_message)
    monkeypatch.setattr(telegram_handler, "send_telegram_document", fake_send_document)
    monkeypatch.setattr(telegram_handler, "answer_telegram_callback_query", fake_answer_callback)
    monkeypatch.setattr(telegram_handler, "_send_diet_pdf", fake_send_diet_pdf)
    monkeypatch.setattr(telegram_handler, "create_new_diet", fake_create_new_diet)

    tr = client.post(
        "/api/auth/token",
        data={
            "username": DEMO_DOCTOR_EMAIL,
            "password": DEMO_DOCTOR_PASSWORD,
        },
    )
    assert tr.status_code == 200, tr.text
    token = tr.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    lp = client.get("/api/patients?page_size=50", headers=headers)
    patient = next(
        p
        for p in lp.json()["items"]
        if p["first_name"] == "Maria" and p["last_name"] == "Lopez"
    )
    patient_id = patient["id"]
    client.post("/api/telegram/binding/reset", headers=headers)
    bind = client.post("/api/telegram/binding/start", headers=headers)
    code = bind.json()["code"]

    chat_id = 776111
    user_id = 995111
    client.post(
        "/api/telegram/webhook",
        json={
            "update_id": 5111,
            "message": {
                "message_id": 111,
                "chat": {"id": chat_id, "type": "private"},
                "from": {"id": user_id, "username": "demo_doc"},
                "text": f"/start {code}",
            },
        },
    )
    client.post(
        "/api/telegram/webhook",
        json={
            "update_id": 5112,
            "message": {
                "message_id": 112,
                "chat": {"id": chat_id, "type": "private"},
                "from": {"id": user_id, "username": "demo_doc"},
                "text": "genera una dieta para Maria",
            },
        },
    )
    client.post(
        "/api/telegram/webhook",
        json={
            "update_id": 5113,
            "message": {
                "message_id": 113,
                "chat": {"id": chat_id, "type": "private"},
                "from": {"id": user_id, "username": "demo_doc"},
                "text": "saltar",
            },
        },
    )
    client.post(
        "/api/telegram/webhook",
        json={
            "update_id": 5114,
            "message": {
                "message_id": 114,
                "chat": {"id": chat_id, "type": "private"},
                "from": {"id": user_id, "username": "demo_doc"},
                "text": "14",
            },
        },
    )
    client.post(
        "/api/telegram/webhook",
        json={
            "update_id": 5115,
            "message": {
                "message_id": 115,
                "chat": {"id": chat_id, "type": "private"},
                "from": {"id": user_id, "username": "demo_doc"},
                "text": "5",
            },
        },
    )
    client.post(
        "/api/telegram/webhook",
        json={
            "update_id": 5116,
            "callback_query": {
                "id": "cb-nl-1",
                "from": {"id": user_id, "username": "demo_doc"},
                "data": f"diet:smd:m:{patient_id}",
                "message": {"chat": {"id": chat_id, "type": "private"}},
            },
        },
    )
    for update_id, message_id, text in [
        (5117, 117, "1800"),
        (5118, 118, "120"),
        (5119, 119, "150"),
        (5120, 120, "60"),
    ]:
        client.post(
            "/api/telegram/webhook",
            json={
                "update_id": update_id,
                "message": {
                    "message_id": message_id,
                    "chat": {"id": chat_id, "type": "private"},
                    "from": {"id": user_id, "username": "demo_doc"},
                    "text": text,
                },
            },
        )
    client.post(
        "/api/telegram/webhook",
        json={
            "update_id": 5121,
            "callback_query": {
                "id": "cb-nl-2",
                "from": {"id": user_id, "username": "demo_doc"},
                "data": f"diet:confirm:{patient_id}",
                "message": {"chat": {"id": chat_id, "type": "private"}},
            },
        },
    )

    preview_msgs = [m for m in sent_messages if "Vista previa" in m["text"]]
    assert preview_msgs
    assert create_calls
    assert create_calls[-1]["meals_per_day"] == 5
    assert create_calls[-1]["strategy_mode"] == "manual"
    assert create_calls[-1]["manual_targets"] == {
        "daily_calories": 1800.0,
        "protein_g": 120.0,
        "carbs_g": 150.0,
        "fat_g": 60.0,
    }
    m_id = re.search(r"Dieta\s*#(\d+)", preview_msgs[-1]["text"])
    assert m_id
    diet_id = int(m_id.group(1))
    client.post(
        "/api/telegram/webhook",
        json={
            "update_id": 5122,
            "callback_query": {
                "id": "cb-nl-3",
                "from": {"id": user_id, "username": "demo_doc"},
                "data": f"diet:preview:approve:{diet_id}",
                "message": {"chat": {"id": chat_id, "type": "private"}},
            },
        },
    )
    assert sent_pdf == [diet_id]


@pytest.mark.usefixtures("seeded")
def test_telegram_guided_flow_rejects_invalid_duration_meals_and_stale_confirm(
    client: TestClient, monkeypatch
):
    sent_messages: list[dict] = []

    async def fake_send_message(chat_id: str, text: str, **kwargs) -> None:
        sent_messages.append({"chat_id": chat_id, "text": text, "kwargs": kwargs})

    async def fake_send_document(*args, **kwargs) -> None:
        return

    async def fake_answer_callback(*args, **kwargs) -> None:
        return

    from app.services import telegram_handler

    monkeypatch.setattr(telegram_handler, "send_telegram_message", fake_send_message)
    monkeypatch.setattr(telegram_handler, "send_telegram_document", fake_send_document)
    monkeypatch.setattr(telegram_handler, "answer_telegram_callback_query", fake_answer_callback)

    tr = client.post(
        "/api/auth/token",
        data={
            "username": DEMO_DOCTOR_EMAIL,
            "password": DEMO_DOCTOR_PASSWORD,
        },
    )
    assert tr.status_code == 200, tr.text
    token = tr.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    lp = client.get("/api/patients?page_size=50", headers=headers)
    patient = next(
        p
        for p in lp.json()["items"]
        if p["first_name"] == "Maria" and p["last_name"] == "Lopez"
    )
    patient_id = patient["id"]
    client.post("/api/telegram/binding/reset", headers=headers)
    bind = client.post("/api/telegram/binding/start", headers=headers)
    code = bind.json()["code"]

    chat_id = 776121
    user_id = 995121
    client.post(
        "/api/telegram/webhook",
        json={
            "update_id": 5131,
            "message": {
                "message_id": 131,
                "chat": {"id": chat_id, "type": "private"},
                "from": {"id": user_id, "username": "demo_doc"},
                "text": f"/start {code}",
            },
        },
    )
    client.post(
        "/api/telegram/webhook",
        json={
            "update_id": 5132,
            "callback_query": {
                "id": "cb-invalid-1",
                "from": {"id": user_id, "username": "demo_doc"},
                "data": f"patient:diet:{patient_id}",
                "message": {"chat": {"id": chat_id, "type": "private"}},
            },
        },
    )
    client.post(
        "/api/telegram/webhook",
        json={
            "update_id": 5133,
            "message": {
                "message_id": 133,
                "chat": {"id": chat_id, "type": "private"},
                "from": {"id": user_id, "username": "demo_doc"},
                "text": "saltar",
            },
        },
    )
    client.post(
        "/api/telegram/webhook",
        json={
            "update_id": 5134,
            "message": {
                "message_id": 134,
                "chat": {"id": chat_id, "type": "private"},
                "from": {"id": user_id, "username": "demo_doc"},
                "text": "8",
            },
        },
    )
    assert any("múltiplo de 7" in m["text"].lower() for m in sent_messages)
    client.post(
        "/api/telegram/webhook",
        json={
            "update_id": 5135,
            "message": {
                "message_id": 135,
                "chat": {"id": chat_id, "type": "private"},
                "from": {"id": user_id, "username": "demo_doc"},
                "text": "14",
            },
        },
    )
    client.post(
        "/api/telegram/webhook",
        json={
            "update_id": 5136,
            "message": {
                "message_id": 136,
                "chat": {"id": chat_id, "type": "private"},
                "from": {"id": user_id, "username": "demo_doc"},
                "text": "6",
            },
        },
    )
    assert any("elige 2, 3, 4 o 5 comidas por día" in m["text"].lower() for m in sent_messages)
    client.post(
        "/api/telegram/webhook",
        json={
            "update_id": 5137,
            "callback_query": {
                "id": "cb-invalid-2",
                "from": {"id": user_id, "username": "demo_doc"},
                "data": f"diet:confirm:{patient_id}",
                "message": {"chat": {"id": chat_id, "type": "private"}},
            },
        },
    )
    assert any("este paso ya no aplica" in m["text"].lower() for m in sent_messages)


@pytest.mark.usefixtures("seeded")
def test_telegram_natural_language_diet_without_patient_shows_next_step(
    client: TestClient, monkeypatch
):
    sent_messages: list[dict] = []

    async def fake_send_message(chat_id: str, text: str, **kwargs) -> None:
        sent_messages.append({"chat_id": chat_id, "text": text, "kwargs": kwargs})

    async def fake_send_document(*args, **kwargs) -> None:
        return

    from app.services import telegram_handler

    monkeypatch.setattr(telegram_handler, "send_telegram_message", fake_send_message)
    monkeypatch.setattr(telegram_handler, "send_telegram_document", fake_send_document)

    tr = client.post(
        "/api/auth/token",
        data={
            "username": DEMO_DOCTOR_EMAIL,
            "password": DEMO_DOCTOR_PASSWORD,
        },
    )
    assert tr.status_code == 200, tr.text
    token = tr.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    client.post("/api/telegram/binding/reset", headers=headers)
    bind = client.post("/api/telegram/binding/start", headers=headers)
    code = bind.json()["code"]

    chat_id = 776151
    user_id = 995151
    client.post(
        "/api/telegram/webhook",
        json={
            "update_id": 5151,
            "message": {
                "message_id": 151,
                "chat": {"id": chat_id, "type": "private"},
                "from": {"id": user_id, "username": "demo_doc"},
                "text": f"/start {code}",
            },
        },
    )
    client.post(
        "/api/telegram/webhook",
        json={
            "update_id": 5152,
            "message": {
                "message_id": 152,
                "chat": {"id": chat_id, "type": "private"},
                "from": {"id": user_id, "username": "demo_doc"},
                "text": "quiero hacer una dieta",
            },
        },
    )

    assert any("quieres crear una dieta" in m["text"].lower() for m in sent_messages)
    assert any("Selecciona un paciente" in m["text"] for m in sent_messages)


@pytest.mark.usefixtures("seeded")
def test_telegram_thanks_is_safe_reply(client: TestClient, monkeypatch):
    sent_messages: list[dict] = []

    async def fake_send_message(chat_id: str, text: str, **kwargs) -> None:
        sent_messages.append({"chat_id": chat_id, "text": text, "kwargs": kwargs})

    async def fake_send_document(*args, **kwargs) -> None:
        return

    from app.services import telegram_handler

    monkeypatch.setattr(telegram_handler, "send_telegram_message", fake_send_message)
    monkeypatch.setattr(telegram_handler, "send_telegram_document", fake_send_document)

    tr = client.post(
        "/api/auth/token",
        data={
            "username": DEMO_DOCTOR_EMAIL,
            "password": DEMO_DOCTOR_PASSWORD,
        },
    )
    assert tr.status_code == 200, tr.text
    token = tr.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    client.post("/api/telegram/binding/reset", headers=headers)
    bind = client.post("/api/telegram/binding/start", headers=headers)
    code = bind.json()["code"]

    chat_id = 776161
    user_id = 995161
    client.post(
        "/api/telegram/webhook",
        json={
            "update_id": 5161,
            "message": {
                "message_id": 161,
                "chat": {"id": chat_id, "type": "private"},
                "from": {"id": user_id, "username": "demo_doc"},
                "text": f"/start {code}",
            },
        },
    )
    sent_messages.clear()
    client.post(
        "/api/telegram/webhook",
        json={
            "update_id": 5162,
            "message": {
                "message_id": 162,
                "chat": {"id": chat_id, "type": "private"},
                "from": {"id": user_id, "username": "demo_doc"},
                "text": "gracias",
            },
        },
    )
    assert any("con gusto" in m["text"].lower() for m in sent_messages)


@pytest.mark.usefixtures("seeded")
def test_telegram_resume_diet_after_missing_height(client: TestClient, monkeypatch):
    sent_messages: list[dict] = []
    create_calls: list[dict] = []

    async def fake_send_message(chat_id: str, text: str, **kwargs) -> None:
        sent_messages.append({"chat_id": chat_id, "text": text, "kwargs": kwargs})

    async def fake_send_document(*args, **kwargs) -> None:
        return

    async def fake_answer_callback(*args, **kwargs) -> None:
        return

    from app.services import telegram_handler

    monkeypatch.setattr(telegram_handler, "send_telegram_message", fake_send_message)
    monkeypatch.setattr(telegram_handler, "send_telegram_document", fake_send_document)
    monkeypatch.setattr(telegram_handler, "answer_telegram_callback_query", fake_answer_callback)

    async def fake_create_new_diet(db, doctor, patient_id, instruction, **kwargs):
        create_calls.append(dict(kwargs))
        if len(create_calls) == 1:
            raise telegram_handler.DietGenerationError(
                "missing_metric",
                "Missing latest height (add a metric)",
                reasons=["Missing latest height (add a metric)"],
            )
        from app.models import Diet
        from app.services.plan_meals import meal_slots_for_count

        meals_per_day = kwargs.get("meals_per_day", 4)
        meal_slots = meal_slots_for_count(meals_per_day)
        diet = Diet(
            patient_id=patient_id,
            doctor_id=doctor.id,
            status="pending_approval",
            title="Plan reanudado",
            summary="Reanudado tras altura",
            structured_plan_json={
                "title": "Plan reanudado",
                "summary": "Reanudado tras altura",
                "daily_calories": 1800,
                "meals_per_day": meals_per_day,
                "meal_slots": meal_slots,
                "days": [
                    {
                        "day": 1,
                        "meals": {slot: f"Meal {slot}" for slot in meal_slots},
                    }
                ],
            },
            notes=instruction,
        )
        db.add(diet)
        await db.flush()
        await db.refresh(diet)
        return diet

    monkeypatch.setattr(telegram_handler, "create_new_diet", fake_create_new_diet)

    tr = client.post(
        "/api/auth/token",
        data={
            "username": DEMO_DOCTOR_EMAIL,
            "password": DEMO_DOCTOR_PASSWORD,
        },
    )
    assert tr.status_code == 200, tr.text
    token = tr.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    lp = client.get("/api/patients?page_size=50", headers=headers)
    patient = next(
        p
        for p in lp.json()["items"]
        if p["first_name"] == "Maria" and p["last_name"] == "Lopez"
    )
    patient_id = patient["id"]
    client.post("/api/telegram/binding/reset", headers=headers)
    bind = client.post("/api/telegram/binding/start", headers=headers)
    code = bind.json()["code"]

    chat_id = 776171
    user_id = 995171
    client.post(
        "/api/telegram/webhook",
        json={
            "update_id": 5171,
            "message": {
                "message_id": 171,
                "chat": {"id": chat_id, "type": "private"},
                "from": {"id": user_id, "username": "demo_doc"},
                "text": f"/start {code}",
            },
        },
    )
    client.post(
        "/api/telegram/webhook",
        json={
            "update_id": 5172,
            "callback_query": {
                "id": "cb-r1",
                "from": {"id": user_id, "username": "demo_doc"},
                "data": f"patient:diet:{patient_id}",
                "message": {"chat": {"id": chat_id, "type": "private"}},
            },
        },
    )
    client.post(
        "/api/telegram/webhook",
        json={
            "update_id": 5173,
            "message": {
                "message_id": 173,
                "chat": {"id": chat_id, "type": "private"},
                "from": {"id": user_id, "username": "demo_doc"},
                "text": "keto",
            },
        },
    )
    client.post(
        "/api/telegram/webhook",
        json={
            "update_id": 51731,
            "message": {
                "message_id": 173,
                "chat": {"id": chat_id, "type": "private"},
                "from": {"id": user_id, "username": "demo_doc"},
                "text": "7",
            },
        },
    )
    client.post(
        "/api/telegram/webhook",
        json={
            "update_id": 51732,
            "callback_query": {
                "id": "cb-r15",
                "from": {"id": user_id, "username": "demo_doc"},
                "data": f"diet:meals:5:{patient_id}",
                "message": {"chat": {"id": chat_id, "type": "private"}},
            },
        },
    )
    client.post(
        "/api/telegram/webhook",
        json={
            "update_id": 51733,
            "callback_query": {
                "id": "cb-r16",
                "from": {"id": user_id, "username": "demo_doc"},
                "data": f"diet:smd:g:{patient_id}",
                "message": {"chat": {"id": chat_id, "type": "private"}},
            },
        },
    )
    client.post(
        "/api/telegram/webhook",
        json={
            "update_id": 51734,
            "callback_query": {
                "id": "cb-r17",
                "from": {"id": user_id, "username": "demo_doc"},
                "data": f"diet:sty:l:{patient_id}",
                "message": {"chat": {"id": chat_id, "type": "private"}},
            },
        },
    )
    for update_id, callback_id, data in [
        (51735, "cb-r18", "diet:mp:s"),
        (51736, "cb-r19", "diet:mc:s"),
        (51737, "cb-r20", "diet:mf:s"),
    ]:
        client.post(
            "/api/telegram/webhook",
            json={
                "update_id": update_id,
                "callback_query": {
                    "id": callback_id,
                    "from": {"id": user_id, "username": "demo_doc"},
                    "data": data,
                    "message": {"chat": {"id": chat_id, "type": "private"}},
                },
            },
        )
    client.post(
        "/api/telegram/webhook",
        json={
            "update_id": 5174,
            "callback_query": {
                "id": "cb-r2",
                "from": {"id": user_id, "username": "demo_doc"},
                "data": f"diet:confirm:{patient_id}",
                "message": {"chat": {"id": chat_id, "type": "private"}},
            },
        },
    )
    assert any("necesito la estatura actual" in m["text"].lower() for m in sent_messages)

    client.post(
        "/api/telegram/webhook",
        json={
            "update_id": 5175,
            "message": {
                "message_id": 175,
                "chat": {"id": chat_id, "type": "private"},
                "from": {"id": user_id, "username": "demo_doc"},
                "text": "165 cm",
            },
        },
    )
    assert any("Confirmar estatura" in m["text"] for m in sent_messages)
    client.post(
        "/api/telegram/webhook",
        json={
            "update_id": 5176,
            "callback_query": {
                "id": "cb-r3",
                "from": {"id": user_id, "username": "demo_doc"},
                "data": f"metric:confirm:{patient_id}:height",
                "message": {"chat": {"id": chat_id, "type": "private"}},
            },
        },
    )
    assert any("ya puedo retomar la dieta" in m["text"].lower() for m in sent_messages)
    client.post(
        "/api/telegram/webhook",
        json={
            "update_id": 5177,
            "callback_query": {
                "id": "cb-r4",
                "from": {"id": user_id, "username": "demo_doc"},
                "data": f"diet:confirm:{patient_id}",
                "message": {"chat": {"id": chat_id, "type": "private"}},
            },
        },
    )
    assert len(create_calls) == 2
    assert create_calls[-1].get("meals_per_day") == 5
    assert create_calls[-1].get("strategy_mode") == "guided"
    assert create_calls[-1].get("diet_style") == "low_carb"
    assert any("Vista previa" in m["text"] for m in sent_messages)

@pytest.mark.usefixtures("seeded")
def test_telegram_diet_quick_adjust_regenerates_preview(client: TestClient, monkeypatch):
    sent_messages: list[dict] = []
    regen_calls: list[str] = []
    create_calls: list[dict] = []

    async def fake_send_message(chat_id: str, text: str, **kwargs) -> None:
        sent_messages.append({"chat_id": chat_id, "text": text, "kwargs": kwargs})

    async def fake_send_document(*args, **kwargs) -> None:
        return

    async def fake_answer_callback(*args, **kwargs) -> None:
        return

    from app.models import Diet
    from app.services import telegram_handler

    monkeypatch.setattr(telegram_handler, "send_telegram_message", fake_send_message)
    monkeypatch.setattr(telegram_handler, "send_telegram_document", fake_send_document)
    monkeypatch.setattr(telegram_handler, "answer_telegram_callback_query", fake_answer_callback)

    async def fake_create_new_diet(
        db, doctor, patient_id, instruction, *, diet_status="generated", **kwargs
    ):
        create_calls.append(dict(kwargs))
        diet = Diet(
            patient_id=patient_id,
            doctor_id=doctor.id,
            status=diet_status,
            title="Plan demo",
            summary="Resumen inicial",
            structured_plan_json={
                "title": "Plan demo",
                "summary": "Resumen inicial",
                "daily_calories": 2000,
                "macros": {"protein_pct": 30, "carbs_pct": 40, "fat_pct": 30},
                "days": [
                    {
                        "day": 1,
                        "breakfast": "A",
                        "lunch": "B",
                        "snack": "C",
                        "dinner": "D",
                    }
                ],
                "recommendations": ["Hidratación adecuada"],
            },
            notes=instruction,
        )
        db.add(diet)
        await db.flush()
        await db.refresh(diet)
        return diet

    async def fake_regenerate_diet(
        db, doctor, diet_id, doctor_instruction, *, diet_status=None, **kwargs
    ):
        regen_calls.append(doctor_instruction or "")
        diet = await db.get(Diet, diet_id)
        assert diet is not None
        diet.summary = "Tras ajuste rápido"
        plan = dict(diet.structured_plan_json or {})
        plan["summary"] = "Tras ajuste rápido"
        diet.structured_plan_json = plan
        if diet_status:
            diet.status = diet_status
        return diet

    monkeypatch.setattr(telegram_handler, "create_new_diet", fake_create_new_diet)
    monkeypatch.setattr(telegram_handler, "regenerate_diet", fake_regenerate_diet)

    tr = client.post(
        "/api/auth/token",
        data={
            "username": DEMO_DOCTOR_EMAIL,
            "password": DEMO_DOCTOR_PASSWORD,
        },
    )
    assert tr.status_code == 200, tr.text
    token = tr.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    lp = client.get("/api/patients?page_size=50", headers=headers)
    assert lp.status_code == 200, lp.text
    patient = next(
        p
        for p in lp.json()["items"]
        if p["first_name"] == "Maria" and p["last_name"] == "Lopez"
    )
    patient_id = patient["id"]
    client.post("/api/telegram/binding/reset", headers=headers)
    bind = client.post("/api/telegram/binding/start", headers=headers)
    code = bind.json()["code"]

    chat_id = 779901
    user_id = 889901
    client.post(
        "/api/telegram/webhook",
        json={
            "update_id": 9001,
            "message": {
                "message_id": 901,
                "chat": {"id": chat_id, "type": "private"},
                "from": {"id": user_id, "username": "demo_doc"},
                "text": f"/start {code}",
            },
        },
    )
    client.post(
        "/api/telegram/webhook",
        json={
            "update_id": 9002,
            "callback_query": {
                "id": "cb-q1",
                "from": {"id": user_id, "username": "demo_doc"},
                "data": f"patient:diet:{patient_id}",
                "message": {"chat": {"id": chat_id, "type": "private"}},
            },
        },
    )
    client.post(
        "/api/telegram/webhook",
        json={
            "update_id": 9003,
            "message": {
                "message_id": 902,
                "chat": {"id": chat_id, "type": "private"},
                "from": {"id": user_id, "username": "demo_doc"},
                "text": "saltar",
            },
        },
    )
    client.post(
        "/api/telegram/webhook",
        json={
            "update_id": 90031,
            "message": {
                "message_id": 902,
                "chat": {"id": chat_id, "type": "private"},
                "from": {"id": user_id, "username": "demo_doc"},
                "text": "7",
            },
        },
    )
    client.post(
        "/api/telegram/webhook",
        json={
            "update_id": 90032,
            "callback_query": {
                "id": "cb-q15",
                "from": {"id": user_id, "username": "demo_doc"},
                "data": f"diet:meals:5:{patient_id}",
                "message": {"chat": {"id": chat_id, "type": "private"}},
            },
        },
    )
    client.post(
        "/api/telegram/webhook",
        json={
            "update_id": 90033,
            "callback_query": {
                "id": "cb-q16",
                "from": {"id": user_id, "username": "demo_doc"},
                "data": f"diet:smd:a:{patient_id}",
                "message": {"chat": {"id": chat_id, "type": "private"}},
            },
        },
    )
    client.post(
        "/api/telegram/webhook",
        json={
            "update_id": 9004,
            "callback_query": {
                "id": "cb-q2",
                "from": {"id": user_id, "username": "demo_doc"},
                "data": f"diet:confirm:{patient_id}",
                "message": {"chat": {"id": chat_id, "type": "private"}},
            },
        },
    )
    preview_msgs = [m for m in sent_messages if "Vista previa" in m["text"]]
    assert preview_msgs
    assert create_calls[-1].get("meals_per_day") == 5
    m_id = re.search(r"Dieta\s*#(\d+)", preview_msgs[-1]["text"])
    assert m_id
    diet_id = int(m_id.group(1))

    client.post(
        "/api/telegram/webhook",
        json={
            "update_id": 9005,
            "callback_query": {
                "id": "cb-q3",
                "from": {"id": user_id, "username": "demo_doc"},
                "data": f"diet:quick:more_prot:{diet_id}",
                "message": {"chat": {"id": chat_id, "type": "private"}},
            },
        },
    )

    assert len(regen_calls) == 1
    assert "Ajuste rápido" in regen_calls[0]
    assert "proteína" in regen_calls[0].lower()
    assert any("Tras ajuste rápido" in m["text"] for m in sent_messages)


@pytest.mark.usefixtures("seeded")
def test_telegram_regenerate_with_duration_callback(client: TestClient, monkeypatch):
    sent_messages: list[dict] = []
    regen_calls: list[dict] = []

    async def fake_send_message(chat_id: str, text: str, **kwargs) -> None:
        sent_messages.append({"chat_id": chat_id, "text": text, "kwargs": kwargs})

    async def fake_send_document(*args, **kwargs) -> None:
        return

    async def fake_answer_callback(*args, **kwargs) -> None:
        return

    from app.models import Diet
    from app.services import telegram_handler

    monkeypatch.setattr(telegram_handler, "send_telegram_message", fake_send_message)
    monkeypatch.setattr(telegram_handler, "send_telegram_document", fake_send_document)
    monkeypatch.setattr(telegram_handler, "answer_telegram_callback_query", fake_answer_callback)

    async def fake_create_new_diet(
        db, doctor, patient_id, instruction, *, diet_status="generated", **kwargs
    ):
        diet = Diet(
            patient_id=patient_id,
            doctor_id=doctor.id,
            status=diet_status,
            title="Plan demo",
            summary="Resumen inicial",
            structured_plan_json={
                "title": "Plan demo",
                "summary": "Resumen inicial",
                "plan_duration_days": 14,
                "daily_calories": 2000,
                "macros": {"protein_pct": 30, "carbs_pct": 40, "fat_pct": 30},
                "days": [
                    {
                        "day": 1,
                        "breakfast": "A",
                        "lunch": "B",
                        "snack": "C",
                        "dinner": "D",
                    }
                ],
                "recommendations": ["Hidratación adecuada"],
            },
            notes=instruction,
        )
        db.add(diet)
        await db.flush()
        await db.refresh(diet)
        return diet

    async def fake_regenerate_diet(
        db, doctor, diet_id, doctor_instruction, *, diet_status=None, **kwargs
    ):
        regen_calls.append(dict(kwargs))
        diet = await db.get(Diet, diet_id)
        assert diet is not None
        diet.summary = "Tras regenerar con duración"
        plan = dict(diet.structured_plan_json or {})
        plan["summary"] = "Tras regenerar con duración"
        plan["plan_duration_days"] = kwargs.get("duration_days") or plan.get(
            "plan_duration_days", 7
        )
        diet.structured_plan_json = plan
        if diet_status:
            diet.status = diet_status
        return diet

    monkeypatch.setattr(telegram_handler, "create_new_diet", fake_create_new_diet)
    monkeypatch.setattr(telegram_handler, "regenerate_diet", fake_regenerate_diet)

    tr = client.post(
        "/api/auth/token",
        data={
            "username": DEMO_DOCTOR_EMAIL,
            "password": DEMO_DOCTOR_PASSWORD,
        },
    )
    assert tr.status_code == 200, tr.text
    token = tr.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    lp = client.get("/api/patients?page_size=50", headers=headers)
    assert lp.status_code == 200, lp.text
    patient = next(
        p
        for p in lp.json()["items"]
        if p["first_name"] == "Maria" and p["last_name"] == "Lopez"
    )
    patient_id = patient["id"]
    client.post("/api/telegram/binding/reset", headers=headers)
    bind = client.post("/api/telegram/binding/start", headers=headers)
    code = bind.json()["code"]

    chat_id = 779902
    user_id = 889902
    client.post(
        "/api/telegram/webhook",
        json={
            "update_id": 9101,
            "message": {
                "message_id": 911,
                "chat": {"id": chat_id, "type": "private"},
                "from": {"id": user_id, "username": "demo_doc"},
                "text": f"/start {code}",
            },
        },
    )
    client.post(
        "/api/telegram/webhook",
        json={
            "update_id": 9102,
            "callback_query": {
                "id": "cb-rd1",
                "from": {"id": user_id, "username": "demo_doc"},
                "data": f"patient:diet:{patient_id}",
                "message": {"chat": {"id": chat_id, "type": "private"}},
            },
        },
    )
    client.post(
        "/api/telegram/webhook",
        json={
            "update_id": 9103,
            "message": {
                "message_id": 912,
                "chat": {"id": chat_id, "type": "private"},
                "from": {"id": user_id, "username": "demo_doc"},
                "text": "saltar",
            },
        },
    )
    client.post(
        "/api/telegram/webhook",
        json={
            "update_id": 9104,
            "callback_query": {
                "id": "cb-rd2",
                "from": {"id": user_id, "username": "demo_doc"},
                "data": f"diet:pickdur:{patient_id}:14",
                "message": {"chat": {"id": chat_id, "type": "private"}},
            },
        },
    )
    client.post(
        "/api/telegram/webhook",
        json={
            "update_id": 91041,
            "callback_query": {
                "id": "cb-rd25",
                "from": {"id": user_id, "username": "demo_doc"},
                "data": f"diet:meals:4:{patient_id}",
                "message": {"chat": {"id": chat_id, "type": "private"}},
            },
        },
    )
    client.post(
        "/api/telegram/webhook",
        json={
            "update_id": 91042,
            "callback_query": {
                "id": "cb-rd26",
                "from": {"id": user_id, "username": "demo_doc"},
                "data": f"diet:smd:a:{patient_id}",
                "message": {"chat": {"id": chat_id, "type": "private"}},
            },
        },
    )
    client.post(
        "/api/telegram/webhook",
        json={
            "update_id": 9105,
            "callback_query": {
                "id": "cb-rd3",
                "from": {"id": user_id, "username": "demo_doc"},
                "data": f"diet:confirm:{patient_id}",
                "message": {"chat": {"id": chat_id, "type": "private"}},
            },
        },
    )
    preview_msgs = [m for m in sent_messages if "Vista previa" in m["text"]]
    assert preview_msgs
    m_id = re.search(r"Dieta\s*#(\d+)", preview_msgs[-1]["text"])
    assert m_id
    diet_id = int(m_id.group(1))

    client.post(
        "/api/telegram/webhook",
        json={
            "update_id": 9106,
            "callback_query": {
                "id": "cb-rd4",
                "from": {"id": user_id, "username": "demo_doc"},
                "data": f"diet:preview:regen:{diet_id}",
                "message": {"chat": {"id": chat_id, "type": "private"}},
            },
        },
    )
    client.post(
        "/api/telegram/webhook",
        json={
            "update_id": 9107,
            "message": {
                "message_id": 913,
                "chat": {"id": chat_id, "type": "private"},
                "from": {"id": user_id, "username": "demo_doc"},
                "text": "saltar",
            },
        },
    )
    client.post(
        "/api/telegram/webhook",
        json={
            "update_id": 9108,
            "callback_query": {
                "id": "cb-rd5",
                "from": {"id": user_id, "username": "demo_doc"},
                "data": f"diet:pickrdur:{diet_id}:28",
                "message": {"chat": {"id": chat_id, "type": "private"}},
            },
        },
    )
    client.post(
        "/api/telegram/webhook",
        json={
            "update_id": 91081,
            "callback_query": {
                "id": "cb-rd55",
                "from": {"id": user_id, "username": "demo_doc"},
                "data": f"diet:meals:5:{patient_id}",
                "message": {"chat": {"id": chat_id, "type": "private"}},
            },
        },
    )
    client.post(
        "/api/telegram/webhook",
        json={
            "update_id": 91082,
            "callback_query": {
                "id": "cb-rd56",
                "from": {"id": user_id, "username": "demo_doc"},
                "data": f"diet:smd:a:{patient_id}",
                "message": {"chat": {"id": chat_id, "type": "private"}},
            },
        },
    )
    client.post(
        "/api/telegram/webhook",
        json={
            "update_id": 91083,
            "callback_query": {
                "id": "cb-rd57",
                "from": {"id": user_id, "username": "demo_doc"},
                "data": f"diet:confirm:{patient_id}",
                "message": {"chat": {"id": chat_id, "type": "private"}},
            },
        },
    )

    assert regen_calls
    assert regen_calls[-1].get("meals_per_day") == 5
    assert regen_calls[-1].get("duration_days") == 28
    assert any("Tras regenerar con duración" in m["text"] for m in sent_messages)


def test_diet_pdf_export(client: TestClient):
    tr = client.post(
        "/api/auth/token",
        data={
            "username": DEMO_DOCTOR_EMAIL,
            "password": DEMO_DOCTOR_PASSWORD,
        },
    )
    assert tr.status_code == 200, tr.text
    token = tr.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    lr = client.get("/api/patients?page_size=50", headers=headers)
    assert lr.status_code == 200
    maria = next(
        p
        for p in lr.json()["items"]
        if p["first_name"] == "Maria" and p["last_name"] == "Lopez"
    )
    gr = client.post(
        "/api/diets/generate",
        headers=headers,
        json={
            "patient_id": maria["id"],
            "doctor_instruction": "E2E PDF smoke",
        },
    )
    if not os.getenv("OPENAI_API_KEY"):
        assert gr.status_code == 503
        pr = client.get("/api/patients?page_size=50", headers=headers)
        diets_r = client.get(
            "/api/diets",
            headers=headers,
            params={"patient_id": maria["id"], "page_size": 5},
        )
        assert diets_r.status_code == 200
        items = diets_r.json().get("items") or []
        if not items:
            pytest.skip("Sin dieta en BD y sin OPENAI_API_KEY — no se prueba PDF")
        diet_id = items[0]["id"]
    else:
        assert gr.status_code == 201, gr.text
        diet_id = gr.json()["id"]

    r = client.get(f"/api/diets/{diet_id}/pdf", headers=headers)
    assert r.status_code == 200, r.text
    assert r.headers.get("content-type", "").startswith("application/pdf")
    assert r.content[:4] == b"%PDF"
