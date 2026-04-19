from typing import List, Optional

from app.logic.profile import norm
from app.models import Patient, PatientMetrics, PatientProfile


def diet_generation_blockers(
    patient: Patient,
    profile: Optional[PatientProfile],
    latest: Optional[PatientMetrics],
) -> List[str]:
    reasons: List[str] = []
    if not patient.birth_date:
        reasons.append("Missing patient birth_date")
    if not patient.sex:
        reasons.append("Missing patient sex")
    if not patient.country or not patient.city:
        reasons.append("Missing patient country or city")
    if not profile:
        reasons.append("Missing clinical profile")
    else:
        if not profile.objective:
            reasons.append("Missing profile objective")
        if not norm(profile.food_allergies):
            reasons.append("Missing food_allergies (use 'none' if none)")
        if not norm(profile.foods_avoided):
            reasons.append("Missing foods_avoided (use 'none' if none)")
    if not latest or latest.weight_kg is None:
        reasons.append("Missing latest weight (add a metric)")
    if not latest or latest.height_cm is None:
        reasons.append("Missing latest height (add a metric)")
    return reasons
