import secrets
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_doctor
from app.core.database import get_db
from app.models import (
    AuditLog,
    Doctor,
    Patient,
    PatientIntakeLink,
    PatientMetrics,
    PatientProfile,
    utcnow,
)
from app.schemas import IntakeLinkCreate, IntakeLinkOut, IntakeLinkPublicMeta, IntakePublicSubmit

router = APIRouter()


@router.get("", response_model=list[IntakeLinkOut])
async def list_links(
    db: AsyncSession = Depends(get_db),
    doctor: Doctor = Depends(get_current_doctor),
):
    result = await db.execute(
        select(PatientIntakeLink)
        .where(PatientIntakeLink.doctor_id == doctor.id)
        .order_by(PatientIntakeLink.created_at.desc())
    )
    return list(result.scalars().all())


@router.post("", response_model=IntakeLinkOut, status_code=status.HTTP_201_CREATED)
async def create_link(
    body: IntakeLinkCreate,
    db: AsyncSession = Depends(get_db),
    doctor: Doctor = Depends(get_current_doctor),
):
    patient = await db.get(Patient, body.patient_id)
    if patient is None or patient.doctor_id != doctor.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found",
        )
    token = secrets.token_urlsafe(32)
    expires_at = utcnow() + timedelta(days=body.expires_in_days)
    link = PatientIntakeLink(
        doctor_id=doctor.id,
        patient_id=body.patient_id,
        token=token,
        expires_at=expires_at,
        max_uses=body.max_uses,
    )
    db.add(link)
    await db.commit()
    await db.refresh(link)
    return link


@router.post("/{link_id}/revoke", response_model=IntakeLinkOut)
async def revoke_link(
    link_id: int,
    db: AsyncSession = Depends(get_db),
    doctor: Doctor = Depends(get_current_doctor),
):
    result = await db.execute(
        select(PatientIntakeLink).where(
            PatientIntakeLink.id == link_id,
            PatientIntakeLink.doctor_id == doctor.id,
        )
    )
    link = result.scalar_one_or_none()
    if link is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Link not found",
        )
    link.status = "revoked"
    link.updated_at = utcnow()
    await db.commit()
    await db.refresh(link)
    return link


@router.get("/public/{token}", response_model=IntakeLinkPublicMeta)
async def public_validate(token: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(PatientIntakeLink).where(PatientIntakeLink.token == token)
    )
    link = result.scalar_one_or_none()
    if link is None:
        return IntakeLinkPublicMeta(valid=False, message="Invalid link")
    now = utcnow()
    if link.status == "revoked":
        return IntakeLinkPublicMeta(valid=False, message="Link revoked")
    if link.expires_at < now:
        return IntakeLinkPublicMeta(
            valid=False,
            expires_at=link.expires_at,
            message="Link expired",
        )
    if link.use_count >= link.max_uses:
        return IntakeLinkPublicMeta(valid=False, message="Link already used")
    patient = await db.get(Patient, link.patient_id)
    return IntakeLinkPublicMeta(
        valid=True,
        expires_at=link.expires_at,
        patient_first_name=patient.first_name if patient else None,
        patient_last_name=patient.last_name if patient else None,
    )


@router.post("/public/{token}/submit", status_code=status.HTTP_200_OK)
async def public_submit(
    token: str,
    body: IntakePublicSubmit,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(PatientIntakeLink).where(PatientIntakeLink.token == token)
    )
    link = result.scalar_one_or_none()
    if link is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid link",
        )
    now = utcnow()
    if link.status == "revoked":
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="Link revoked")
    if link.expires_at < now:
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="Link expired")
    if link.use_count >= link.max_uses:
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="Link already used")

    patient = await db.get(Patient, link.patient_id)
    if patient is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found",
        )

    patient.first_name = body.first_name
    patient.last_name = body.last_name
    patient.birth_date = body.birth_date
    patient.sex = body.sex
    patient.whatsapp = body.whatsapp
    patient.email = str(body.email) if body.email else None
    patient.country = body.country
    patient.city = body.city
    patient.source = "intake_link"
    patient.updated_at = utcnow()

    prof_result = await db.execute(
        select(PatientProfile).where(PatientProfile.patient_id == patient.id)
    )
    profile = prof_result.scalar_one_or_none()
    if profile is None:
        profile = PatientProfile(patient_id=patient.id)
        db.add(profile)

    profile.objective = body.objective
    profile.diseases = body.diseases
    profile.medications = body.medications
    profile.food_allergies = body.food_allergies
    profile.foods_avoided = body.foods_avoided
    profile.medical_history = body.medical_history
    profile.dietary_style = body.dietary_style
    profile.food_preferences = body.food_preferences
    profile.disliked_foods = body.disliked_foods
    profile.meal_schedule = body.meal_schedule
    profile.water_intake_liters = body.water_intake_liters
    profile.stress_level = body.stress_level
    profile.sleep_quality = body.sleep_quality
    profile.sleep_hours = body.sleep_hours
    profile.budget_level = body.budget_level
    profile.activity_level = body.activity_level
    profile.adherence_level = body.adherence_level
    profile.exercise_frequency_per_week = body.exercise_frequency_per_week
    profile.exercise_type = body.exercise_type
    profile.extra_notes = body.extra_notes
    profile.completed_by_patient = True
    profile.completed_at = utcnow()
    profile.updated_at = utcnow()

    metric = PatientMetrics(
        patient_id=patient.id,
        weight_kg=body.weight_kg,
        height_cm=body.height_cm,
        neck_cm=body.neck_cm,
        chest_cm=body.chest_cm,
        waist_cm=body.waist_cm,
        hip_cm=body.hip_cm,
        leg_cm=body.leg_cm,
        calf_cm=body.calf_cm,
        recorded_at=utcnow(),
        source="intake_link",
    )
    db.add(metric)

    link.use_count += 1
    link.last_used_at = utcnow()
    link.updated_at = utcnow()
    if link.use_count >= link.max_uses:
        link.status = "completed"

    db.add(
        AuditLog(
            doctor_id=link.doctor_id,
            action="intake_submit",
            entity_type="patient",
            entity_id=patient.id,
            payload_json={"intake_link_id": link.id},
        )
    )
    await db.commit()
    return {"ok": True}
