from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any, Optional

from sqlalchemy import asc, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Diet, DietVersion, Patient, PatientMetrics, PatientProfile, utcnow


def _f(v: Decimal | float | None) -> float | None:
    if v is None:
        return None
    return float(v)


def calc_age(birth_date: date | None) -> int | None:
    if birth_date is None:
        return None
    today = utcnow().date()
    age = today.year - birth_date.year
    if (today.month, today.day) < (birth_date.month, birth_date.day):
        age -= 1
    return age


async def latest_metric(db: AsyncSession, patient_id: int) -> Optional[PatientMetrics]:
    result = await db.execute(
        select(PatientMetrics)
        .where(PatientMetrics.patient_id == patient_id)
        .order_by(PatientMetrics.recorded_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def get_doctor_patient(db: AsyncSession, doctor_id: int, patient_id: int) -> Patient | None:
    result = await db.execute(
        select(Patient).where(Patient.id == patient_id, Patient.doctor_id == doctor_id)
    )
    return result.scalar_one_or_none()


async def search_doctor_patients(
    db: AsyncSession,
    doctor_id: int,
    query: str | None = None,
    *,
    include_archived: bool = False,
    page: int = 1,
    page_size: int = 10,
) -> tuple[list[Patient], int]:
    conditions = [Patient.doctor_id == doctor_id]
    if not include_archived:
        conditions.append(Patient.is_archived.is_(False))
    if query:
        term = f"%{query.strip()}%"
        conditions.append(
            or_(
                Patient.first_name.ilike(term),
                Patient.last_name.ilike(term),
                func.concat(Patient.first_name, " ", Patient.last_name).ilike(term),
            )
        )
    count_stmt = select(func.count()).select_from(Patient).where(*conditions)
    total = int((await db.execute(count_stmt)).scalar_one())
    result = await db.execute(
        select(Patient)
        .where(*conditions)
        .order_by(Patient.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return list(result.scalars().all()), total


async def get_patient_profile(db: AsyncSession, patient_id: int) -> PatientProfile | None:
    result = await db.execute(
        select(PatientProfile).where(PatientProfile.patient_id == patient_id)
    )
    return result.scalar_one_or_none()


async def list_patient_diets(
    db: AsyncSession,
    doctor_id: int,
    patient_id: int,
    *,
    page: int = 1,
    page_size: int = 10,
) -> tuple[list[Diet], int]:
    conditions = [
        Diet.doctor_id == doctor_id,
        Diet.patient_id == patient_id,
        Diet.status != "discarded",
    ]
    count_stmt = select(func.count()).select_from(Diet).where(*conditions)
    total = int((await db.execute(count_stmt)).scalar_one())
    result = await db.execute(
        select(Diet)
        .where(*conditions)
        .order_by(Diet.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return list(result.scalars().all()), total


async def list_diet_versions(
    db: AsyncSession,
    doctor_id: int,
    diet_id: int,
) -> list[DietVersion]:
    diet = await db.get(Diet, diet_id)
    if diet is None or diet.doctor_id != doctor_id:
        return []
    result = await db.execute(
        select(DietVersion)
        .where(DietVersion.diet_id == diet_id)
        .order_by(DietVersion.version_number.asc())
    )
    return list(result.scalars().all())


async def get_doctor_diet(db: AsyncSession, doctor_id: int, diet_id: int) -> Diet | None:
    diet = await db.get(Diet, diet_id)
    if diet is None or diet.doctor_id != doctor_id:
        return None
    return diet


async def update_patient_fields(
    db: AsyncSession,
    patient: Patient,
    *,
    city: str | None = None,
    whatsapp: str | None = None,
    email: str | None = None,
    archive: bool | None = None,
) -> Patient:
    if city is not None:
        patient.city = city
    if whatsapp is not None:
        patient.whatsapp = whatsapp
    if email is not None:
        patient.email = email
    if archive is not None:
        patient.is_archived = archive
        if archive:
            patient.is_active = False
    patient.updated_at = utcnow()
    await db.flush()
    return patient


async def add_patient_metric(
    db: AsyncSession,
    patient_id: int,
    *,
    weight_kg: float | None = None,
    height_cm: float | None = None,
    notes: str | None = None,
    source: str = "telegram",
) -> PatientMetrics:
    prev = await latest_metric(db, patient_id)
    merged_weight = weight_kg if weight_kg is not None else _f(prev.weight_kg) if prev else None
    merged_height = height_cm if height_cm is not None else _f(prev.height_cm) if prev else None
    metric = PatientMetrics(
        patient_id=patient_id,
        weight_kg=merged_weight,
        height_cm=merged_height,
        recorded_at=utcnow(),
        source=source,
        notes=notes,
    )
    db.add(metric)
    await db.flush()
    return metric


def patient_identity_label(patient: Patient) -> str:
    age = calc_age(patient.birth_date)
    parts = [f"{patient.first_name} {patient.last_name}".strip(), f"#{patient.id}"]
    if age is not None:
        parts.append(f"{age} años")
    if patient.city:
        parts.append(patient.city)
    return " · ".join(parts)


def format_patient_summary(
    patient: Patient,
    *,
    profile: PatientProfile | None,
    metric: PatientMetrics | None,
) -> str:
    lines = [
        f"Paciente: {patient_identity_label(patient)}",
        f"Sexo: {patient.sex or '—'}",
        f"Fecha de nacimiento: {patient.birth_date or '—'}",
        f"Activo: {'sí' if patient.is_active else 'no'} · Archivado: {'sí' if patient.is_archived else 'no'}",
    ]
    if metric:
        lines.append(
            f"Última métrica: peso {_f(metric.weight_kg) or '—'} kg · talla {_f(metric.height_cm) or '—'} cm · {metric.recorded_at.date()}"
        )
    if profile:
        lines.append(f"Objetivo: {profile.objective or '—'}")
        if profile.food_allergies:
            lines.append(f"Alergias: {profile.food_allergies}")
        if profile.diseases:
            lines.append(f"Condiciones: {profile.diseases}")
    return "\n".join(lines)


async def doctor_diet_count(db: AsyncSession, doctor_id: int) -> int:
    return int(
        (
            await db.execute(
                select(func.count())
                .select_from(Diet)
                .where(
                    Diet.doctor_id == doctor_id,
                    Diet.status.in_(["generated", "approved"]),
                )
            )
        ).scalar_one()
    )


async def doctor_patient_stats(db: AsyncSession, doctor_id: int) -> dict[str, Any]:
    total = int(
        (
            await db.execute(
                select(func.count()).select_from(Patient).where(Patient.doctor_id == doctor_id)
            )
        ).scalar_one()
    )
    first_result = await db.execute(
        select(Patient)
        .where(Patient.doctor_id == doctor_id)
        .order_by(asc(Patient.created_at))
        .limit(1)
    )
    last_result = await db.execute(
        select(Patient)
        .where(Patient.doctor_id == doctor_id)
        .order_by(desc(Patient.created_at))
        .limit(1)
    )
    first = first_result.scalar_one_or_none()
    last = last_result.scalar_one_or_none()
    return {
        "total": total,
        "first_patient": first,
        "last_patient": last,
    }
