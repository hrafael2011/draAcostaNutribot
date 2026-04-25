"""
Datos de demostración: doctora + pacientes listos para generar dieta (perfil + métricas).
Idempotente: no duplica doctor ni pacientes por nombre.
"""
from __future__ import annotations

from datetime import date
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash
from app.models import Doctor, Patient, PatientMetrics, PatientProfile, utcnow

DEMO_DOCTOR_EMAIL = "demo.doctor@diet-agent.local"
DEMO_DOCTOR_PASSWORD = "DemoDoc2026!"
DEMO_DOCTOR_NAME = "Dra. Demo Acosta"


async def _get_or_create_doctor(session: AsyncSession) -> Doctor:
    result = await session.execute(
        select(Doctor).where(Doctor.email == DEMO_DOCTOR_EMAIL.lower())
    )
    doctor = result.scalar_one_or_none()
    if doctor:
        doctor.role = doctor.role or "doctor"
        doctor.must_change_password = False
        doctor.is_active = True
        return doctor
    doctor = Doctor(
        full_name=DEMO_DOCTOR_NAME,
        email=DEMO_DOCTOR_EMAIL.lower(),
        phone="+18095550001",
        hashed_password=get_password_hash(DEMO_DOCTOR_PASSWORD),
        role="doctor",
        must_change_password=False,
    )
    session.add(doctor)
    await session.flush()
    return doctor


async def _ensure_patient_bundle(
    session: AsyncSession,
    doctor: Doctor,
    spec: dict[str, Any],
) -> Patient:
    result = await session.execute(
        select(Patient).where(
            Patient.doctor_id == doctor.id,
            Patient.first_name == spec["first_name"],
            Patient.last_name == spec["last_name"],
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        existing.birth_date = spec["birth_date"]
        existing.sex = spec["sex"]
        existing.whatsapp = spec.get("whatsapp")
        existing.email = spec.get("email")
        existing.country = spec["country"]
        existing.city = spec["city"]
        existing.source = "admin"

        profile_result = await session.execute(
            select(PatientProfile).where(PatientProfile.patient_id == existing.id)
        )
        profile = profile_result.scalar_one_or_none()
        if profile is None:
            profile = PatientProfile(patient_id=existing.id)
            session.add(profile)
        profile.objective = spec["objective"]
        profile.diseases = spec.get("diseases")
        profile.medications = spec.get("medications")
        profile.food_allergies = spec["food_allergies"]
        profile.foods_avoided = spec["foods_avoided"]
        profile.medical_history = spec.get("medical_history")
        profile.dietary_style = spec.get("dietary_style")
        profile.food_preferences = spec.get("food_preferences")
        profile.disliked_foods = spec.get("disliked_foods")
        profile.activity_level = spec.get("activity_level", "moderate")
        profile.stress_level = spec.get("stress_level", 3)
        profile.sleep_quality = spec.get("sleep_quality", 3)
        profile.sleep_hours = spec.get("sleep_hours", 7.0)
        profile.budget_level = spec.get("budget_level", "medium")
        profile.adherence_level = spec.get("adherence_level", 4)
        profile.exercise_frequency_per_week = spec.get("exercise_frequency_per_week", 3)
        profile.exercise_type = spec.get("exercise_type", "walking")
        profile.extra_notes = spec.get("extra_notes")
        profile.water_intake_liters = spec.get("water_intake_liters", 2.0)
        profile.completed_by_patient = True
        profile.completed_at = utcnow()

        metrics_result = await session.execute(
            select(PatientMetrics)
            .where(PatientMetrics.patient_id == existing.id)
            .order_by(PatientMetrics.recorded_at.desc())
            .limit(1)
        )
        latest_metric = metrics_result.scalar_one_or_none()
        m = spec["metrics"]
        if latest_metric is None:
            latest_metric = PatientMetrics(patient_id=existing.id)
            session.add(latest_metric)
        latest_metric.weight_kg = m["weight_kg"]
        latest_metric.height_cm = m["height_cm"]
        latest_metric.waist_cm = m.get("waist_cm")
        latest_metric.hip_cm = m.get("hip_cm")
        latest_metric.recorded_at = utcnow()
        latest_metric.source = "admin"
        latest_metric.notes = "Demo seed"
        return existing

    patient = Patient(
        doctor_id=doctor.id,
        first_name=spec["first_name"],
        last_name=spec["last_name"],
        birth_date=spec["birth_date"],
        sex=spec["sex"],
        whatsapp=spec.get("whatsapp"),
        email=spec.get("email"),
        country=spec["country"],
        city=spec["city"],
        source="admin",
    )
    session.add(patient)
    await session.flush()

    profile = PatientProfile(
        patient_id=patient.id,
        objective=spec["objective"],
        diseases=spec.get("diseases"),
        medications=spec.get("medications"),
        food_allergies=spec["food_allergies"],
        foods_avoided=spec["foods_avoided"],
        medical_history=spec.get("medical_history"),
        dietary_style=spec.get("dietary_style"),
        food_preferences=spec.get("food_preferences"),
        disliked_foods=spec.get("disliked_foods"),
        activity_level=spec.get("activity_level", "moderate"),
        stress_level=spec.get("stress_level", 3),
        sleep_quality=spec.get("sleep_quality", 3),
        sleep_hours=spec.get("sleep_hours", 7.0),
        budget_level=spec.get("budget_level", "medium"),
        adherence_level=spec.get("adherence_level", 4),
        exercise_frequency_per_week=spec.get("exercise_frequency_per_week", 3),
        exercise_type=spec.get("exercise_type", "walking"),
        extra_notes=spec.get("extra_notes"),
        water_intake_liters=spec.get("water_intake_liters", 2.0),
        completed_by_patient=True,
        completed_at=utcnow(),
    )
    session.add(profile)

    m = spec["metrics"]
    metric = PatientMetrics(
        patient_id=patient.id,
        weight_kg=m["weight_kg"],
        height_cm=m["height_cm"],
        waist_cm=m.get("waist_cm"),
        hip_cm=m.get("hip_cm"),
        recorded_at=utcnow(),
        source="admin",
        notes="Demo seed",
    )
    session.add(metric)
    return patient


PATIENT_SPECS: list[dict[str, Any]] = [
    {
        "first_name": "Maria",
        "last_name": "Lopez",
        "birth_date": date(1991, 5, 10),
        "sex": "female",
        "whatsapp": "+18095550111",
        "email": "maria.lopez.demo@example.com",
        "country": "Republica Dominicana",
        "city": "Santo Domingo",
        "objective": "lose_weight",
        "diseases": "Hipotiroidismo leve (controlada)",
        "medications": "Levotiroxina 50mcg",
        "food_allergies": "none",
        "foods_avoided": "bebidas azucaradas, frituras frecuentes",
        "dietary_style": "omnivora",
        "food_preferences": "pollo, arroz, ensaladas, frutas tropicales",
        "disliked_foods": "higado, berenjena",
        "activity_level": "low",
        "budget_level": "medium",
        "metrics": {"weight_kg": 74.5, "height_cm": 164, "waist_cm": 88, "hip_cm": 104},
    },
    {
        "first_name": "Carlos",
        "last_name": "Ruiz",
        "birth_date": date(1988, 3, 15),
        "sex": "male",
        "whatsapp": "+18095550222",
        "email": "carlos.ruiz.demo@example.com",
        "country": "Republica Dominicana",
        "city": "Santiago",
        "objective": "gain_muscle",
        "diseases": "none",
        "medications": "none",
        "food_allergies": "mani",
        "foods_avoided": "lacteos enteros, mani, mariscos",
        "dietary_style": "high_protein",
        "food_preferences": "huevo, avena, pescado, legumbres",
        "disliked_foods": "okra",
        "activity_level": "high",
        "budget_level": "medium_high",
        "metrics": {"weight_kg": 82.0, "height_cm": 178, "waist_cm": 90, "hip_cm": 98},
    },
]


async def run_demo_seed() -> dict[str, Any]:
    from app.core.database import AsyncSessionLocal

    out: dict[str, Any] = {"doctor_email": DEMO_DOCTOR_EMAIL, "patients": []}
    async with AsyncSessionLocal() as session:
        doctor = await _get_or_create_doctor(session)
        out["doctor_id"] = doctor.id
        for spec in PATIENT_SPECS:
            p = await _ensure_patient_bundle(session, doctor, spec)
            out["patients"].append(
                {"id": p.id, "name": f"{p.first_name} {p.last_name}"}
            )
        await session.commit()
    return out
