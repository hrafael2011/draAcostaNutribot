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
            reasons.append("Faltan alergias alimentarias (escribe 'ninguna' si no aplica)")
        if not norm(profile.foods_avoided):
            reasons.append("Faltan alimentos a evitar (escribe 'ninguno' si no aplica)")
    if not latest or latest.weight_kg is None:
        reasons.append("Missing latest weight (add a metric)")
    if not latest or latest.height_cm is None:
        reasons.append("Missing latest height (add a metric)")
    return reasons
