from __future__ import annotations

import json
import re
from typing import Any, Optional

from openai import AsyncOpenAI

from app.core.config import settings


def rule_based_intent(text: str) -> tuple[str, str, dict[str, Any]]:
    """
    Deterministic intent: (intent, policy, entities).
    policy: safe | guided_diet | needs_patient | unmapped
    """
    t = text.strip().lower()
    entities: dict[str, Any] = {}
    if not t:
        return "unknown", "unmapped", entities

    if any(
        t.startswith(p)
        for p in (
            "hola",
            "buenos",
            "buenas",
            "hey",
            "hi",
            "saludos",
            "saludo",
            "qué tal",
            "que tal",
        )
    ):
        return "greeting", "safe", entities
    if any(
        phrase in t
        for phrase in (
            "gracias",
            "muchas gracias",
            "te agradezco",
            "perfecto gracias",
            "ok gracias",
            "genial gracias",
            "listo gracias",
            "graciass",
            "bye",
            "chao",
        )
    ):
        return "thanks", "safe", entities
    if any(k in t for k in ("menú", "menu", "opciones")):
        return "menu", "safe", entities
    if any(k in t for k in ("ayuda", "help", "comandos")):
        return "help", "safe", entities
    if any(k in t for k in ("buscar", "encuentra")) and "paciente" not in t:
        return "search", "safe", entities

    if "historial" in t or (
        any(x in t for x in ("dietas", "planes"))
        and any(x in t for x in ("paciente", "de ", "del ", "para "))
    ):
        return "patient_history", "needs_patient", entities

    if any(
        x in t
        for x in (
            "información del paciente",
            "informacion del paciente",
            "datos del paciente",
            "ficha del paciente",
            "ver paciente",
            "muéstrame al paciente",
            "muestrame al paciente",
        )
    ):
        return "patient_show", "needs_patient", entities

    if any(
        k in t
        for k in (
            "editar",
            "actualizar datos",
            "cambiar datos",
            "modificar datos",
            "información de",
            "informacion de",
        )
    ):
        if not any(
            k in t
            for k in (
                "peso",
                "estatura",
                "altura",
                "talla",
                "lb",
                "kg",
                "cm",
                "metro",
                "pies",
                "pulg",
                "libras",
            )
        ):
            return "patient_edit", "needs_patient", entities

    if ("cuánt" in t or "cuant" in t) and any(
        k in t for k in ("dieta", "dietas", "plan", "planes")
    ):
        return "stats_diets", "safe", entities
    if ("cuánt" in t or "cuant" in t) and "pacient" in t:
        return "stats_patients", "safe", entities
    if any(k in t for k in ("estadístic", "estadistic", "resumen")) and (
        "pacient" in t or "dieta" in t or "consultorio" in t
    ):
        return "stats_summary", "safe", entities

    if any(k in t for k in ("paciente", "pacientes", "listar pacientes", "mis pacientes")):
        return "patients", "safe", entities

    if any(k in t for k in ("dieta", "plan nutricional", "plan alimenticio")) or (
        "plan" in t and "aliment" in t
    ):
        return "diet", "guided_diet", entities

    if any(
        k in t
        for k in (
            "actualiza",
            "actualizar",
            "cambia",
            "cambiar",
            "editar",
            "agrega",
            "agregar",
            "añade",
            "añadir",
            "pone",
            "poner",
            "falta",
            "faltar",
            "necesito",
            "quiero agregar",
            "quiero poner",
            "peso",
            "estatura",
            "altura",
            "talla",
            "ciudad",
        )
    ):
        return "possible_mutation", "needs_patient", entities

    if re.search(r"\b\d+\b", text):
        return "unknown", "ambiguous_entity", entities
    return "unknown", "unmapped", entities


def _parse_json_response(raw: str) -> dict[str, Any]:
    s = raw.strip()
    if s.startswith("```"):
        s = re.sub(r"^```(?:json)?\s*", "", s)
        s = re.sub(r"\s*```$", "", s)
    return json.loads(s)


ALLOWED_LLM_INTENTS = frozenset(
    {
        "greeting",
        "thanks",
        "menu",
        "help",
        "search",
        "patients",
        "stats_patients",
        "stats_diets",
        "stats_summary",
        "patient_history",
        "patient_show",
        "patient_edit",
        "possible_mutation",
        "diet",
        "unknown",
    }
)


async def classify_intent_llm(text: str) -> Optional[dict[str, Any]]:
    if not settings.OPENAI_API_KEY:
        return None
    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    system = (
        "Clasificador de intenciones para un bot de Telegram de una doctora. "
        "Responde SOLO JSON con keys: intent (string), patient_name (string|null), "
        "confidence (number 0-1). "
        f"intent debe ser uno de: {', '.join(sorted(ALLOWED_LLM_INTENTS))}. "
        "No inventes datos clínicos ni nombres de pacientes reales: solo extrae lo que el usuario escribió. "
        "Si no estás seguro, usa intent unknown."
    )
    resp = await client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": text[:2000]},
        ],
        response_format={"type": "json_object"},
        temperature=0.1,
    )
    content = resp.choices[0].message.content
    if not content:
        return None
    data = _parse_json_response(content)
    intent = data.get("intent", "unknown")
    if intent not in ALLOWED_LLM_INTENTS:
        intent = "unknown"
    return {
        "intent": intent,
        "patient_name": data.get("patient_name"),
        "confidence": float(data.get("confidence") or 0),
    }
