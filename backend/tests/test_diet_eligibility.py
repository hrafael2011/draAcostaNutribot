from datetime import date, datetime, timezone

from app.logic.diet_eligibility import diet_generation_blockers
from app.models import Patient, PatientMetrics, PatientProfile


def _ts():
    return datetime.now(timezone.utc)


def test_no_blockers_when_complete():
    p = Patient(
        doctor_id=1,
        first_name="Ana",
        last_name="Lopez",
        birth_date=date(1991, 5, 10),
        sex="female",
        country="DO",
        city="Santo Domingo",
        source="admin",
    )
    pr = PatientProfile(
        patient_id=1,
        objective="lose_weight",
        food_allergies="none",
        foods_avoided="none",
    )
    m = PatientMetrics(
        patient_id=1,
        weight_kg=74.5,
        height_cm=164,
        recorded_at=_ts(),
        source="admin",
    )
    assert diet_generation_blockers(p, pr, m) == []


def test_blockers_when_missing_metrics():
    p = Patient(
        doctor_id=1,
        first_name="Ana",
        last_name="Lopez",
        birth_date=date(1991, 5, 10),
        sex="female",
        country="DO",
        city="Santo Domingo",
        source="admin",
    )
    pr = PatientProfile(
        patient_id=1,
        objective="lose_weight",
        food_allergies="none",
        foods_avoided="none",
    )
    reasons = diet_generation_blockers(p, pr, None)
    assert any("weight" in r.lower() for r in reasons)
    assert any("height" in r.lower() for r in reasons)
