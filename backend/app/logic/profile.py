from typing import Optional

from app.models import Patient, PatientMetrics, PatientProfile


def norm(s: Optional[str]) -> str:
    return (s or "").strip().lower()


def is_profile_complete(
    patient: Patient,
    profile: Optional[PatientProfile],
    latest: Optional[PatientMetrics],
) -> bool:
    if not patient.birth_date or not patient.sex or not patient.country or not patient.city:
        return False
    if not profile or not profile.objective:
        return False
    if not norm(profile.food_allergies) or not norm(profile.foods_avoided):
        return False
    if not latest or latest.weight_kg is None or latest.height_cm is None:
        return False
    return True
