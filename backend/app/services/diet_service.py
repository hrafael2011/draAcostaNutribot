from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any, Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.logic.diet_duration import (
    apply_plan_duration_metadata,
    duration_from_existing_plan,
    validate_duration_days,
)
from app.logic.diet_eligibility import diet_generation_blockers
from app.nutrition import compute_nutrition
from app.nutrition.input_builder import NutritionInputBuildError, build_nutrition_input_from_bundle
from app.nutrition.plan_merge import merge_nutrition_into_plan, nutrition_targets_for_llm
from app.models import (
    AuditLog,
    Diet,
    DietVersion,
    Doctor,
    Patient,
    PatientMetrics,
    PatientProfile,
    utcnow,
)
from app.services.diet_openai import generate_diet_plan_json
from app.services.plan_meals import meal_slots_for_count, normalize_meals_per_day


class DietGenerationError(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        reasons: Optional[list[str]] = None,
    ):
        self.code = code
        self.message = message
        self.reasons = reasons or []
        super().__init__(message)


def _json_safe(v: Any) -> Any:
    if isinstance(v, Decimal):
        return float(v)
    if isinstance(v, date):
        return v.isoformat()
    return v


async def _latest_metric(
    db: AsyncSession, patient_id: int
) -> Optional[PatientMetrics]:
    r = await db.execute(
        select(PatientMetrics)
        .where(PatientMetrics.patient_id == patient_id)
        .order_by(PatientMetrics.recorded_at.desc())
        .limit(1)
    )
    return r.scalar_one_or_none()


async def load_patient_bundle(
    db: AsyncSession, patient_id: int, doctor_id: int
) -> Tuple[Patient, Optional[PatientProfile], Optional[PatientMetrics]]:
    patient = await db.get(Patient, patient_id)
    if patient is None or patient.doctor_id != doctor_id:
        raise DietGenerationError("not_found", "Patient not found")
    pr = await db.execute(
        select(PatientProfile).where(PatientProfile.patient_id == patient_id)
    )
    profile = pr.scalar_one_or_none()
    metrics = await _latest_metric(db, patient_id)
    return patient, profile, metrics


def build_snapshot(
    patient: Patient,
    profile: Optional[PatientProfile],
    metrics: Optional[PatientMetrics],
) -> dict[str, Any]:
    snap: dict[str, Any] = {
        "patient": {
            "id": patient.id,
            "first_name": patient.first_name,
            "last_name": patient.last_name,
            "birth_date": _json_safe(patient.birth_date),
            "sex": patient.sex,
            "country": patient.country,
            "city": patient.city,
            "email": patient.email,
            "whatsapp": patient.whatsapp,
        },
        "profile": None,
        "latest_metrics": None,
    }
    if profile:
        snap["profile"] = {
            "objective": profile.objective,
            "diseases": profile.diseases,
            "medications": profile.medications,
            "food_allergies": profile.food_allergies,
            "foods_avoided": profile.foods_avoided,
            "medical_history": profile.medical_history,
            "dietary_style": profile.dietary_style,
            "food_preferences": profile.food_preferences,
            "disliked_foods": profile.disliked_foods,
            "activity_level": profile.activity_level,
            "budget_level": profile.budget_level,
            "stress_level": profile.stress_level,
            "sleep_quality": profile.sleep_quality,
            "sleep_hours": _json_safe(profile.sleep_hours),
            "water_intake_liters": _json_safe(profile.water_intake_liters),
            "adherence_level": profile.adherence_level,
            "exercise_frequency_per_week": profile.exercise_frequency_per_week,
            "exercise_type": profile.exercise_type,
            "extra_notes": profile.extra_notes,
        }
    if metrics:
        snap["latest_metrics"] = {
            "weight_kg": _json_safe(metrics.weight_kg),
            "height_cm": _json_safe(metrics.height_cm),
            "waist_cm": _json_safe(metrics.waist_cm),
            "hip_cm": _json_safe(metrics.hip_cm),
            "recorded_at": metrics.recorded_at.isoformat(),
        }
    return snap


async def _generate_plan_with_nutrition_engine(
    patient: Patient,
    profile: PatientProfile,
    metrics: PatientMetrics,
    doctor_instruction: Optional[str],
    *,
    duration_days: int,
    meals_per_day: int = 4,
    strategy_mode: str = "auto",
    diet_style: Optional[str] = None,
    macro_mode: Optional[dict[str, Any]] = None,
    manual_targets: Optional[dict[str, Any]] = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    duration_days = validate_duration_days(duration_days)
    snapshot = build_snapshot(patient, profile, metrics)
    try:
        n_in = build_nutrition_input_from_bundle(
            patient,
            profile,
            metrics,
            strategy_mode=strategy_mode,
            diet_style=diet_style,
            macro_mode=macro_mode,
            manual_targets=manual_targets,
        )
    except NutritionInputBuildError as e:
        raise DietGenerationError(
            e.code,
            e.message,
            [e.message],
        ) from e
    n_out = compute_nutrition(n_in)
    if n_out.blocks_generation():
        blocking = [a.message_es for a in n_out.alerts if a.blocks_generation]
        raise DietGenerationError(
            "nutrition_blocked",
            blocking[0] if blocking else "Generación bloqueada por seguridad nutricional.",
            blocking or None,
        )
    targets = nutrition_targets_for_llm(n_out)
    normalized_meals_per_day = normalize_meals_per_day(meals_per_day)
    targets["meals_per_day"] = normalized_meals_per_day
    targets["meal_slots"] = meal_slots_for_count(normalized_meals_per_day)
    if strategy_mode != "auto":
        # Mantener contexto explícito para redacción del menú (motor sigue siendo autoridad numérica).
        targets["strategy_mode"] = strategy_mode
    if diet_style:
        targets["diet_style"] = diet_style
    if macro_mode:
        targets["macro_mode"] = macro_mode
    if manual_targets:
        targets["manual_targets"] = manual_targets
    plan = await generate_diet_plan_json(
        snapshot,
        doctor_instruction,
        nutrition_targets=targets,
    )
    plan = merge_nutrition_into_plan(plan, n_out, nutrition_input=n_in)
    plan = apply_plan_duration_metadata(plan, duration_days)
    return snapshot, plan


async def create_new_diet(
    db: AsyncSession,
    doctor: Doctor,
    patient_id: int,
    doctor_instruction: Optional[str],
    *,
    diet_status: str = "generated",
    duration_days: int = 7,
    meals_per_day: int = 4,
    strategy_mode: str = "auto",
    diet_style: Optional[str] = None,
    macro_mode: Optional[dict[str, Any]] = None,
    manual_targets: Optional[dict[str, Any]] = None,
) -> Diet:
    duration_days = validate_duration_days(duration_days)
    patient, profile, metrics = await load_patient_bundle(db, patient_id, doctor.id)
    blockers = diet_generation_blockers(patient, profile, metrics)
    if blockers:
        raise DietGenerationError(
            "incomplete_profile",
            "Patient data incomplete for diet generation",
            blockers,
        )
    if profile is None or metrics is None:
        raise DietGenerationError(
            "incomplete_profile",
            "Patient data incomplete for diet generation",
            ["Missing profile or metrics"],
        )
    try:
        snapshot, plan = await _generate_plan_with_nutrition_engine(
            patient,
            profile,
            metrics,
            doctor_instruction,
            duration_days=duration_days,
            meals_per_day=meals_per_day,
            strategy_mode=strategy_mode,
            diet_style=diet_style,
            macro_mode=macro_mode,
            manual_targets=manual_targets,
        )
    except DietGenerationError:
        raise
    except RuntimeError as e:
        raise DietGenerationError("openai_config", str(e)) from e
    except Exception as e:
        raise DietGenerationError(
            "openai_error",
            f"Model error: {e}",
        ) from e

    title = (plan.get("title") or "Plan nutricional")[:160]
    summary = plan.get("summary") or ""

    diet = Diet(
        patient_id=patient_id,
        doctor_id=doctor.id,
        status=diet_status,
        title=title,
        summary=summary,
        structured_plan_json=plan,
        notes=doctor_instruction,
    )
    db.add(diet)
    await db.flush()
    ver = DietVersion(
        diet_id=diet.id,
        version_number=1,
        doctor_instruction=doctor_instruction,
        input_snapshot_json=snapshot,
        output_json=plan,
    )
    db.add(ver)
    db.add(
        AuditLog(
            doctor_id=doctor.id,
            action="diet_generate",
            entity_type="diet",
            entity_id=diet.id,
            payload_json={"patient_id": patient_id},
        )
    )
    return diet


async def approve_diet_preview(
    db: AsyncSession,
    doctor: Doctor,
    diet_id: int,
) -> Diet:
    diet = await db.get(Diet, diet_id)
    if diet is None or diet.doctor_id != doctor.id:
        raise DietGenerationError("not_found", "Diet not found")
    if diet.status != "pending_approval":
        raise DietGenerationError(
            "invalid_state",
            "La dieta no está pendiente de aprobación",
        )
    diet.status = "generated"
    diet.updated_at = utcnow()
    db.add(
        AuditLog(
            doctor_id=doctor.id,
            action="diet_approve",
            entity_type="diet",
            entity_id=diet.id,
            payload_json=None,
        )
    )
    return diet


async def discard_diet_preview(
    db: AsyncSession,
    doctor: Doctor,
    diet_id: int,
) -> Diet:
    diet = await db.get(Diet, diet_id)
    if diet is None or diet.doctor_id != doctor.id:
        raise DietGenerationError("not_found", "Diet not found")
    if diet.status != "pending_approval":
        raise DietGenerationError(
            "invalid_state",
            "La dieta no está pendiente de aprobación",
        )
    diet.status = "discarded"
    diet.updated_at = utcnow()
    db.add(
        AuditLog(
            doctor_id=doctor.id,
            action="diet_discard_preview",
            entity_type="diet",
            entity_id=diet.id,
            payload_json=None,
        )
    )
    return diet


async def regenerate_diet(
    db: AsyncSession,
    doctor: Doctor,
    diet_id: int,
    doctor_instruction: Optional[str],
    *,
    diet_status: Optional[str] = None,
    duration_days: Optional[int] = None,
    meals_per_day: Optional[int] = None,
    strategy_mode: str = "auto",
    diet_style: Optional[str] = None,
    macro_mode: Optional[dict[str, Any]] = None,
    manual_targets: Optional[dict[str, Any]] = None,
) -> Diet:
    diet = await db.get(Diet, diet_id)
    if diet is None or diet.doctor_id != doctor.id:
        raise DietGenerationError("not_found", "Diet not found")

    resolved_duration = (
        validate_duration_days(duration_days)
        if duration_days is not None
        else duration_from_existing_plan(diet.structured_plan_json)
    )
    resolved_meals_per_day = normalize_meals_per_day(
        meals_per_day
        if meals_per_day is not None
        else (
            diet.structured_plan_json.get("meals_per_day")
            if isinstance(diet.structured_plan_json, dict)
            else None
        )
    )

    patient, profile, metrics = await load_patient_bundle(db, diet.patient_id, doctor.id)
    blockers = diet_generation_blockers(patient, profile, metrics)
    if blockers:
        raise DietGenerationError(
            "incomplete_profile",
            "Patient data incomplete for diet generation",
            blockers,
        )
    if profile is None or metrics is None:
        raise DietGenerationError(
            "incomplete_profile",
            "Patient data incomplete for diet generation",
            ["Missing profile or metrics"],
        )
    try:
        snapshot, plan = await _generate_plan_with_nutrition_engine(
            patient,
            profile,
            metrics,
            doctor_instruction,
            duration_days=resolved_duration,
            meals_per_day=resolved_meals_per_day,
            strategy_mode=strategy_mode,
            diet_style=diet_style,
            macro_mode=macro_mode,
            manual_targets=manual_targets,
        )
    except DietGenerationError:
        raise
    except RuntimeError as e:
        raise DietGenerationError("openai_config", str(e)) from e
    except Exception as e:
        raise DietGenerationError("openai_error", f"Model error: {e}") from e

    title = (plan.get("title") or diet.title or "Plan nutricional")[:160]
    summary = plan.get("summary") or ""

    rmax = await db.execute(
        select(func.coalesce(func.max(DietVersion.version_number), 0)).where(
            DietVersion.diet_id == diet.id
        )
    )
    next_v = int(rmax.scalar_one()) + 1

    diet.title = title
    diet.summary = summary
    diet.structured_plan_json = plan
    diet.status = diet_status if diet_status is not None else "generated"
    if doctor_instruction is not None:
        diet.notes = doctor_instruction
    diet.updated_at = utcnow()

    ver = DietVersion(
        diet_id=diet.id,
        version_number=next_v,
        doctor_instruction=doctor_instruction,
        input_snapshot_json=snapshot,
        output_json=plan,
    )
    db.add(ver)
    db.add(
        AuditLog(
            doctor_id=doctor.id,
            action="diet_regenerate",
            entity_type="diet",
            entity_id=diet.id,
            payload_json={"version": next_v},
        )
    )
    return diet
