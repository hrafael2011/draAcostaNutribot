import json
import re
from typing import Any, Optional

from openai import AsyncOpenAI

from app.core.config import settings
from app.services.plan_meals import normalize_plan_meal_metadata


def _parse_json_response(raw: str) -> dict[str, Any]:
    s = raw.strip()
    if s.startswith("```"):
        s = re.sub(r"^```(?:json)?\s*", "", s)
        s = re.sub(r"\s*```$", "", s)
    return json.loads(s)


def _normalize_plan_output(
    plan: dict[str, Any],
    *,
    nutrition_targets: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    out = dict(plan)
    out["title"] = (out.get("title") or "Plan nutricional personalizado").strip()
    out["summary"] = (
        out.get("summary")
        or "Plan nutricional de 7 días, adaptado al contexto clínico y objetivo del paciente."
    ).strip()

    recs = out.get("recommendations")
    normalized_recs: list[str] = []
    if isinstance(recs, str) and recs.strip():
        normalized_recs = [recs.strip()]
    elif isinstance(recs, list):
        normalized_recs = [
            str(item).strip() for item in recs if isinstance(item, str) and item.strip()
        ]

    if not normalized_recs:
        normalized_recs = [
            "Hidratación: distribuir el consumo de agua de forma constante durante el día, ajustado al peso, estatura, edad y actividad física.",
            "Actividad física: mantener ejercicio regular según tolerancia y condición clínica.",
            "Descanso: priorizar sueño nocturno suficiente y pausas de recuperación durante el día.",
            "Adherencia: planificar comidas con anticipación y mantener horarios consistentes.",
        ]
    out["recommendations"] = normalized_recs
    requested_meals_per_day = None
    if isinstance(nutrition_targets, dict):
        requested_meals_per_day = nutrition_targets.get("meals_per_day")
    return normalize_plan_meal_metadata(
        out,
        requested_meals_per_day=requested_meals_per_day,
    )


async def generate_diet_plan_json(
    patient_snapshot: dict,
    doctor_instruction: Optional[str],
    *,
    nutrition_targets: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    if not settings.OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is not set")

    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    system = (
        "Eres un asistente experto en planificación nutricional (no sustituyes criterio médico). "
        "Responde SOLO con JSON válido (sin markdown, sin texto extra). "
        "TODO el contenido textual debe estar en español, incluyendo título, resumen, comidas, "
        "recomendaciones y nombres de alimentos. "
        "El JSON debe incluir obligatoriamente: "
        '"title" (string), "summary" (string, 2-5 frases), '
        '"daily_calories" (number), '
        '"macros" (objeto con protein_pct, carbs_pct, fat_pct numéricos y suma aproximada 100), '
        '"meals_per_day" (integer entre 2 y 5), '
        '"meal_slots" (array ordenado de strings; usa solo estos ids válidos: '
        'breakfast, mid_morning_snack, lunch, snack, dinner), '
        '"days" (array EXACTO de 7 objetos; cada objeto con "day" entero 1-7 y '
        '"meals" como objeto cuyas claves sean EXACTAMENTE las de meal_slots y cuyos valores sean strings), '
        '"recommendations" (array de 4 a 6 strings profesionales). '
        "IMPORTANTE — porciones: en cada entrada de meals debes indicar "
        "la cantidad o porción de CADA alimento. Usa gramos (g), mililitros (ml), tazas, cucharadas "
        "o unidades según corresponda. "
        "Ejemplo correcto: '150 g de pechuga de pollo a la plancha, 1 taza (180 g) de arroz integral "
        "cocido, ensalada de tomate y pepino con 1 cdta de aceite de oliva.' "
        "Ejemplo incorrecto (sin cantidades): 'Pollo a la plancha con arroz y ensalada.' "
        "En recommendations debes incluir explícitamente: "
        "1) hidratación sugerida en litros/día según peso, estatura, edad y actividad; "
        "2) recomendación de actividad física adaptada al objetivo y nivel de actividad; "
        "3) recomendación de descanso/recuperación diaria; "
        "4) consejos de adherencia. "
        "La nota del doctor (doctor_instruction) es opcional y solo orienta la composición del plan; "
        "NO copies textualmente esa nota en recommendations. "
        "Si nutrition_targets incluye strategy_mode / applied_mode / applied_preferences, "
        "úsalos para orientar el tipo de comidas y el estilo del plan, pero SIN alterar "
        "los números oficiales de calorías y macros. "
        "Si nutrition_targets incluye meals_per_day y meal_slots, respétalos EXACTAMENTE; "
        "no agregues ni elimines slots y haz que days.meals siga ese orden clínico. "
        "Respeta alergias, alimentos evitados, enfermedades, medicación, estilo dietario, presupuesto "
        "y nivel de actividad provistos en patient_context. "
        "Usa alimentos culturalmente apropiados para el país del paciente cuando sea posible. "
        "No inventes diagnósticos ni datos clínicos faltantes."
    )
    if nutrition_targets:
        system += (
            " Si nutrition_targets está presente en el mensaje de usuario, sus valores "
            "son la única fuente válida para daily_calories y para macros (protein_pct, "
            "carbs_pct, fat_pct): copia esos números exactamente en tu respuesta JSON. "
            "El menú (days) y el texto deben ser coherentes con esos objetivos."
        )
    user_payload: dict[str, Any] = {
        "patient_context": patient_snapshot,
        "doctor_instruction": doctor_instruction or "",
    }
    if nutrition_targets is not None:
        user_payload["nutrition_targets"] = nutrition_targets
    user = json.dumps(user_payload, default=str)

    resp = await client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        response_format={"type": "json_object"},
        temperature=0.4,
    )
    content = resp.choices[0].message.content
    if not content:
        raise RuntimeError("Empty model response")
    return _normalize_plan_output(
        _parse_json_response(content),
        nutrition_targets=nutrition_targets,
    )
