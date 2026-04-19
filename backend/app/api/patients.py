from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_doctor
from app.core.database import get_db
from app.logic.diet_duration import optional_plan_duration_days
from app.logic.profile import is_profile_complete, norm
from app.models import (
    Diet,
    Doctor,
    Patient,
    PatientMetrics,
    PatientProfile,
    utcnow,
)
from app.schemas import (
    PaginatedPatients,
    PatientCreate,
    PatientMetricsCreate,
    PatientMetricsOut,
    PatientOut,
    PatientProfileOut,
    PatientProfileUpsert,
    PatientSummaryOut,
    PatientUpdate,
)

router = APIRouter()


async def _get_patient_for_doctor(
    db: AsyncSession, doctor_id: int, patient_id: int
) -> Patient:
    result = await db.execute(
        select(Patient).where(
            Patient.id == patient_id,
            Patient.doctor_id == doctor_id,
        )
    )
    patient = result.scalar_one_or_none()
    if patient is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")
    return patient


async def _latest_metrics(
    db: AsyncSession, patient_id: int
) -> Optional[PatientMetrics]:
    result = await db.execute(
        select(PatientMetrics)
        .where(PatientMetrics.patient_id == patient_id)
        .order_by(PatientMetrics.recorded_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


@router.get("", response_model=PaginatedPatients)
async def list_patients(
    db: AsyncSession = Depends(get_db),
    doctor: Doctor = Depends(get_current_doctor),
    search: Optional[str] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    conditions = [Patient.doctor_id == doctor.id]
    if status_filter == "archived":
        conditions.append(Patient.is_archived.is_(True))
    elif status_filter == "active":
        conditions.append(Patient.is_archived.is_(False))
        conditions.append(Patient.is_active.is_(True))
    if search:
        term = f"%{search.strip()}%"
        conditions.append(
            or_(
                Patient.first_name.ilike(term),
                Patient.last_name.ilike(term),
            )
        )
    count_stmt = select(func.count()).select_from(Patient).where(*conditions)
    total = (await db.execute(count_stmt)).scalar_one()
    stmt = (
        select(Patient)
        .where(*conditions)
        .order_by(Patient.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(stmt)
    items = result.scalars().all()
    return PaginatedPatients(
        items=[PatientOut.model_validate(p) for p in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("", response_model=PatientOut, status_code=status.HTTP_201_CREATED)
async def create_patient(
    body: PatientCreate,
    db: AsyncSession = Depends(get_db),
    doctor: Doctor = Depends(get_current_doctor),
):
    patient = Patient(
        doctor_id=doctor.id,
        first_name=body.first_name,
        last_name=body.last_name,
        birth_date=body.birth_date,
        sex=body.sex,
        whatsapp=body.whatsapp,
        email=str(body.email) if body.email else None,
        country=body.country,
        city=body.city,
        source="admin",
    )
    db.add(patient)
    await db.commit()
    await db.refresh(patient)
    return patient


@router.get("/{patient_id}", response_model=PatientOut)
async def get_patient(
    patient_id: int,
    db: AsyncSession = Depends(get_db),
    doctor: Doctor = Depends(get_current_doctor),
):
    patient = await _get_patient_for_doctor(db, doctor.id, patient_id)
    return patient


@router.patch("/{patient_id}", response_model=PatientOut)
async def update_patient(
    patient_id: int,
    body: PatientUpdate,
    db: AsyncSession = Depends(get_db),
    doctor: Doctor = Depends(get_current_doctor),
):
    patient = await _get_patient_for_doctor(db, doctor.id, patient_id)
    data = body.model_dump(exclude_unset=True)
    if "email" in data and data["email"] is not None:
        data["email"] = str(data["email"])
    for key, value in data.items():
        setattr(patient, key, value)
    patient.updated_at = utcnow()
    await db.commit()
    await db.refresh(patient)
    return patient


@router.get("/{patient_id}/profile", response_model=PatientProfileOut)
async def get_profile(
    patient_id: int,
    db: AsyncSession = Depends(get_db),
    doctor: Doctor = Depends(get_current_doctor),
):
    await _get_patient_for_doctor(db, doctor.id, patient_id)
    result = await db.execute(
        select(PatientProfile).where(PatientProfile.patient_id == patient_id)
    )
    profile = result.scalar_one_or_none()
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
    return profile


@router.put("/{patient_id}/profile", response_model=PatientProfileOut)
async def put_profile(
    patient_id: int,
    body: PatientProfileUpsert,
    db: AsyncSession = Depends(get_db),
    doctor: Doctor = Depends(get_current_doctor),
):
    await _get_patient_for_doctor(db, doctor.id, patient_id)
    result = await db.execute(
        select(PatientProfile).where(PatientProfile.patient_id == patient_id)
    )
    profile = result.scalar_one_or_none()
    payload = body.model_dump()
    if profile is None:
        profile = PatientProfile(patient_id=patient_id, **payload)
        db.add(profile)
    else:
        for key, value in payload.items():
            setattr(profile, key, value)
        profile.updated_at = utcnow()
    await db.commit()
    await db.refresh(profile)
    return profile


@router.patch("/{patient_id}/profile", response_model=PatientProfileOut)
async def patch_profile(
    patient_id: int,
    body: PatientProfileUpsert,
    db: AsyncSession = Depends(get_db),
    doctor: Doctor = Depends(get_current_doctor),
):
    await _get_patient_for_doctor(db, doctor.id, patient_id)
    result = await db.execute(
        select(PatientProfile).where(PatientProfile.patient_id == patient_id)
    )
    profile = result.scalar_one_or_none()
    if profile is None:
        profile = PatientProfile(patient_id=patient_id)
        db.add(profile)
    data = body.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(profile, key, value)
    profile.updated_at = utcnow()
    await db.commit()
    await db.refresh(profile)
    return profile


@router.get("/{patient_id}/metrics", response_model=list[PatientMetricsOut])
async def list_metrics(
    patient_id: int,
    db: AsyncSession = Depends(get_db),
    doctor: Doctor = Depends(get_current_doctor),
):
    await _get_patient_for_doctor(db, doctor.id, patient_id)
    result = await db.execute(
        select(PatientMetrics)
        .where(PatientMetrics.patient_id == patient_id)
        .order_by(PatientMetrics.recorded_at.desc())
    )
    rows = result.scalars().all()
    return [PatientMetricsOut.model_validate(r) for r in rows]


@router.post(
    "/{patient_id}/metrics",
    response_model=PatientMetricsOut,
    status_code=status.HTTP_201_CREATED,
)
async def add_metrics(
    patient_id: int,
    body: PatientMetricsCreate,
    db: AsyncSession = Depends(get_db),
    doctor: Doctor = Depends(get_current_doctor),
):
    await _get_patient_for_doctor(db, doctor.id, patient_id)
    recorded = body.recorded_at or utcnow()
    metric = PatientMetrics(
        patient_id=patient_id,
        weight_kg=body.weight_kg,
        height_cm=body.height_cm,
        neck_cm=body.neck_cm,
        chest_cm=body.chest_cm,
        waist_cm=body.waist_cm,
        hip_cm=body.hip_cm,
        leg_cm=body.leg_cm,
        calf_cm=body.calf_cm,
        recorded_at=recorded,
        source=body.source or "admin",
        notes=body.notes,
    )
    db.add(metric)
    await db.commit()
    await db.refresh(metric)
    return metric


@router.get("/{patient_id}/summary", response_model=PatientSummaryOut)
async def patient_summary(
    patient_id: int,
    db: AsyncSession = Depends(get_db),
    doctor: Doctor = Depends(get_current_doctor),
):
    patient = await _get_patient_for_doctor(db, doctor.id, patient_id)
    result = await db.execute(
        select(PatientProfile).where(PatientProfile.patient_id == patient_id)
    )
    profile = result.scalar_one_or_none()
    latest = await _latest_metrics(db, patient_id)
    diet_result = await db.execute(
        select(Diet)
        .where(Diet.patient_id == patient_id)
        .order_by(Diet.created_at.desc())
        .limit(1)
    )
    latest_diet = diet_result.scalar_one_or_none()

    fa = norm(profile.food_allergies if profile else None)
    has_allergies = bool(fa and fa not in ("none", "ninguna", "n/a"))
    dis = norm(profile.diseases if profile else None)
    has_diseases = bool(dis and dis not in ("none", "ninguna", "n/a"))

    complete = is_profile_complete(patient, profile, latest)
    latest_metrics_out = None
    if latest:
        latest_metrics_out = PatientSummaryOut.LatestMetricsMini(
            weight_kg=float(latest.weight_kg) if latest.weight_kg is not None else None,
            height_cm=float(latest.height_cm) if latest.height_cm is not None else None,
        )
    latest_diet_out = None
    if latest_diet:
        latest_diet_out = PatientSummaryOut.LatestDietMini(
            id=latest_diet.id,
            created_at=latest_diet.created_at,
            plan_duration_days=optional_plan_duration_days(
                latest_diet.structured_plan_json
            ),
        )
    return PatientSummaryOut(
        patient=PatientSummaryOut.PatientMini(
            id=patient.id,
            full_name=f"{patient.first_name} {patient.last_name}".strip(),
        ),
        latest_metrics=latest_metrics_out,
        profile_flags=PatientSummaryOut.ProfileFlags(
            has_allergies=has_allergies,
            has_diseases=has_diseases,
            is_profile_complete=complete,
        ),
        latest_diet=latest_diet_out,
    )
