from datetime import timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_doctor
from app.core.database import get_db
from app.models import AuditLog, Diet, Doctor, Patient, PatientProfile, utcnow
from app.schemas import DashboardSummary

router = APIRouter()


@router.get("/summary", response_model=DashboardSummary)
async def summary(
    db: AsyncSession = Depends(get_db),
    doctor: Doctor = Depends(get_current_doctor),
):
    now = utcnow()
    since = now - timedelta(days=30)

    total_patients = (
        await db.execute(
            select(func.count())
            .select_from(Patient)
            .where(Patient.doctor_id == doctor.id)
        )
    ).scalar_one()

    new_patients_30d = (
        await db.execute(
            select(func.count())
            .select_from(Patient)
            .where(Patient.doctor_id == doctor.id, Patient.created_at >= since)
        )
    ).scalar_one()

    incomplete_profiles = (
        await db.execute(
            select(func.count())
            .select_from(Patient)
            .outerjoin(
                PatientProfile,
                PatientProfile.patient_id == Patient.id,
            )
            .where(
                Patient.doctor_id == doctor.id,
                or_(
                    PatientProfile.id.is_(None),
                    PatientProfile.completed_by_patient.is_(False),
                ),
            )
        )
    ).scalar_one()

    diets_generated = (
        await db.execute(
            select(func.count())
            .select_from(Diet)
            .where(
                Diet.doctor_id == doctor.id,
                Diet.status.in_(["generated", "approved"]),
            )
        )
    ).scalar_one()

    activity_result = await db.execute(
        select(AuditLog)
        .where(AuditLog.doctor_id == doctor.id)
        .order_by(AuditLog.created_at.desc())
        .limit(10)
    )
    logs = activity_result.scalars().all()
    latest_activity = [
        {
            "id": log.id,
            "action": log.action,
            "entity_type": log.entity_type,
            "entity_id": log.entity_id,
            "created_at": log.created_at.isoformat(),
        }
        for log in logs
    ]

    return DashboardSummary(
        total_patients=total_patients,
        new_patients_30d=new_patients_30d,
        incomplete_profiles=incomplete_profiles,
        diets_generated=diets_generated,
        latest_activity=latest_activity,
    )
