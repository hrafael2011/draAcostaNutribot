"""Textos y teclados inline del flujo de dieta en Telegram (sin estado ni red)."""

from __future__ import annotations

from app.logic.diet_duration import QUICK_PLAN_DURATION_DAYS
from app.models import Patient


def diet_duration_prompt_message() -> str:
    return (
        "¿Cuántos días en total debe seguir el paciente este plan?\n"
        "Puedes pulsar un botón abajo o escribir un múltiplo de 7 (ej.: 7, 14, 21) "
        "o las semanas (ej.: «3 semanas»).\n"
        "Responde «7» o «una semana» para una sola semana."
    )


def diet_duration_choice_markup(patient_id: int) -> dict:
    rows: list[list[dict]] = []
    row: list[dict] = []
    for d in QUICK_PLAN_DURATION_DAYS:
        row.append(
            {
                "text": f"{d} d",
                "callback_data": f"diet:pickdur:{patient_id}:{d}",
            }
        )
        if len(row) == 3:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([{"text": "Cancelar", "callback_data": "flow:cancel"}])
    return {"inline_keyboard": rows}


def diet_regen_duration_choice_markup(diet_id: int) -> dict:
    rows: list[list[dict]] = []
    row: list[dict] = []
    for d in QUICK_PLAN_DURATION_DAYS:
        row.append(
            {
                "text": f"{d} d",
                "callback_data": f"diet:pickrdur:{diet_id}:{d}",
            }
        )
        if len(row) == 3:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([{"text": "Cancelar", "callback_data": "flow:cancel"}])
    return {"inline_keyboard": rows}


def diet_meals_prompt_message() -> str:
    return (
        "¿Cuántas comidas hará el paciente por día?\n"
        "Esto define la estructura clínica del menú diario."
    )


def diet_meals_choice_markup(patient_id: int) -> dict:
    return {
        "inline_keyboard": [
            [
                {"text": "2 comidas", "callback_data": f"diet:meals:2:{patient_id}"},
                {"text": "3 comidas", "callback_data": f"diet:meals:3:{patient_id}"},
            ],
            [
                {"text": "4 comidas", "callback_data": f"diet:meals:4:{patient_id}"},
                {"text": "5 comidas", "callback_data": f"diet:meals:5:{patient_id}"},
            ],
            [{"text": "Cancelar", "callback_data": "flow:cancel"}],
        ]
    }


def diet_confirm_body(
    patient: Patient,
    *,
    instruction_summary: str,
    duration_days: int,
    strategy_summary_lines: list[str] | None = None,
    is_regenerate: bool = False,
) -> str:
    weeks = max(1, duration_days // 7)
    strat = ""
    if strategy_summary_lines:
        strat = "\n".join(strategy_summary_lines) + "\n"
    head = (
        f"Confirmar regeneración del borrador para {patient.first_name} {patient.last_name}.\n"
        if is_regenerate
        else f"Confirmar generación de dieta para {patient.first_name} {patient.last_name}.\n"
    )
    return (
        f"{head}"
        f"Duración total: {duration_days} días ({weeks} semana(s)); el plan describe un ciclo base de 7 días.\n"
        f"{strat}"
        f"Instrucción: {instruction_summary}"
    )


def diet_strategy_mode_prompt_message() -> str:
    return (
        "Elige cómo calcular los objetivos nutricionales del plan:\n"
        "• Automático: el motor actual (por defecto).\n"
        "• Guiado: estilo (p. ej. baja en carbohidratos) y preferencias de macros.\n"
        "• Manual: puedes fijar calorías y/o gramos de macros (con advertencias si aplica)."
    )


def diet_strategy_mode_markup(patient_id: int) -> dict:
    return {
        "inline_keyboard": [
            [
                {
                    "text": "Automático",
                    "callback_data": f"diet:smd:a:{patient_id}",
                },
                {
                    "text": "Guiado",
                    "callback_data": f"diet:smd:g:{patient_id}",
                },
            ],
            [
                {
                    "text": "Manual",
                    "callback_data": f"diet:smd:m:{patient_id}",
                },
            ],
            [{"text": "Cancelar", "callback_data": "flow:cancel"}],
        ]
    }


def diet_strategy_style_prompt_message() -> str:
    return (
        "Estilo de dieta (opcional). Elige una opción o «Sin estilo específico» "
        "para dejar solo las preferencias de macros."
    )


def diet_strategy_style_markup(patient_id: int) -> dict:
    return {
        "inline_keyboard": [
            [
                {
                    "text": "Sin estilo",
                    "callback_data": f"diet:sty:n:{patient_id}",
                },
                {
                    "text": "Equilibrada",
                    "callback_data": f"diet:sty:b:{patient_id}",
                },
            ],
            [
                {
                    "text": "Baja carbos",
                    "callback_data": f"diet:sty:l:{patient_id}",
                },
                {
                    "text": "Alta carbos",
                    "callback_data": f"diet:sty:h:{patient_id}",
                },
            ],
            [
                {
                    "text": "Alta proteína",
                    "callback_data": f"diet:sty:p:{patient_id}",
                },
                {
                    "text": "Mediterránea",
                    "callback_data": f"diet:sty:m:{patient_id}",
                },
            ],
            [{"text": "Cancelar", "callback_data": "flow:cancel"}],
        ]
    }


def diet_macro_protein_prompt_message() -> str:
    return "Preferencia de proteína (modo guiado). «Omitir» = no fijar preferencia para este macro."


def diet_macro_protein_markup() -> dict:
    return {
        "inline_keyboard": [
            [
                {"text": "Baja", "callback_data": "diet:mp:l"},
                {"text": "Normal", "callback_data": "diet:mp:n"},
                {"text": "Alta", "callback_data": "diet:mp:h"},
            ],
            [{"text": "Omitir", "callback_data": "diet:mp:s"}],
            [{"text": "Cancelar", "callback_data": "flow:cancel"}],
        ]
    }


def diet_macro_carbs_prompt_message() -> str:
    return "Preferencia de carbohidratos (modo guiado). «Omitir» = no fijar preferencia para este macro."


def diet_macro_carbs_markup() -> dict:
    return {
        "inline_keyboard": [
            [
                {"text": "Baja", "callback_data": "diet:mc:l"},
                {"text": "Normal", "callback_data": "diet:mc:n"},
                {"text": "Alta", "callback_data": "diet:mc:h"},
            ],
            [{"text": "Omitir", "callback_data": "diet:mc:s"}],
            [{"text": "Cancelar", "callback_data": "flow:cancel"}],
        ]
    }


def diet_macro_fat_prompt_message() -> str:
    return "Preferencia de grasas (modo guiado). «Omitir» = no fijar preferencia para este macro."


def diet_macro_fat_markup() -> dict:
    return {
        "inline_keyboard": [
            [
                {"text": "Baja", "callback_data": "diet:mf:l"},
                {"text": "Normal", "callback_data": "diet:mf:n"},
                {"text": "Alta", "callback_data": "diet:mf:h"},
            ],
            [{"text": "Omitir", "callback_data": "diet:mf:s"}],
            [{"text": "Cancelar", "callback_data": "flow:cancel"}],
        ]
    }


def diet_manual_kcal_prompt_message() -> str:
    return (
        "Modo manual: envía las calorías objetivo por día (número entero, ej. 1800), "
        "o escribe «saltar» para no fijar calorías."
    )


def diet_manual_protein_prompt_message() -> str:
    return (
        "Proteína en g/día (opcional). Envía un número o «saltar»."
    )


def diet_manual_carbs_prompt_message() -> str:
    return (
        "Carbohidratos en g/día (opcional). Envía un número o «saltar»."
    )


def diet_manual_fat_prompt_message() -> str:
    return "Grasas en g/día (opcional). Envía un número o «saltar»."


def diet_confirm_markup(patient_id: int) -> dict:
    return {
        "inline_keyboard": [
            [
                {"text": "Confirmar generación", "callback_data": f"diet:confirm:{patient_id}"},
                {"text": "Cancelar", "callback_data": f"diet:cancel:{patient_id}"},
            ]
        ]
    }


def diet_note_offer_markup(patient_id: int) -> dict:
    return {
        "inline_keyboard": [
            [
                {
                    "text": "Sí, agregar nota",
                    "callback_data": f"diet:note:yes:{patient_id}",
                },
                {
                    "text": "No, sin nota",
                    "callback_data": f"diet:note:no:{patient_id}",
                },
            ],
            [{"text": "Cancelar", "callback_data": f"diet:cancel:{patient_id}"}],
        ]
    }


def diet_preview_markup(diet_id: int) -> dict:
    return {
        "inline_keyboard": [
            [
                {
                    "text": "Aprobar y enviar PDF",
                    "callback_data": f"diet:preview:approve:{diet_id}",
                },
            ],
            [
                {
                    "text": "Ajustes rápidos",
                    "callback_data": f"diet:preview:quickmenu:{diet_id}",
                },
            ],
            [
                {
                    "text": "Regenerar con nueva nota",
                    "callback_data": f"diet:preview:regen:{diet_id}",
                },
                {
                    "text": "Descartar borrador",
                    "callback_data": f"diet:preview:discard:{diet_id}",
                },
            ],
        ]
    }
