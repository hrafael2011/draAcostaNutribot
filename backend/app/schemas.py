from datetime import date, datetime
from typing import Optional, Any, List, Literal
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class DoctorCreate(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    phone: Optional[str] = None


class DoctorOut(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    phone: Optional[str] = None
    telegram_user_id: Optional[str] = None
    telegram_username: Optional[str] = None
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class PatientCreate(BaseModel):
    first_name: str
    last_name: str
    birth_date: Optional[date] = None
    sex: Optional[str] = None
    whatsapp: Optional[str] = None
    email: Optional[EmailStr] = None
    country: Optional[str] = None
    city: Optional[str] = None


class PatientOut(BaseModel):
    id: int
    doctor_id: int
    first_name: str
    last_name: str
    birth_date: Optional[date] = None
    sex: Optional[str] = None
    whatsapp: Optional[str] = None
    email: Optional[EmailStr] = None
    country: Optional[str] = None
    city: Optional[str] = None
    source: str
    is_active: bool
    is_archived: bool = False

    model_config = ConfigDict(from_attributes=True)


class PatientUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    birth_date: Optional[date] = None
    sex: Optional[str] = None
    whatsapp: Optional[str] = None
    email: Optional[EmailStr] = None
    country: Optional[str] = None
    city: Optional[str] = None
    is_active: Optional[bool] = None
    is_archived: Optional[bool] = None


class PatientProfileOut(BaseModel):
    id: int
    patient_id: int
    objective: Optional[str] = None
    diseases: Optional[str] = None
    medications: Optional[str] = None
    food_allergies: Optional[str] = None
    foods_avoided: Optional[str] = None
    medical_history: Optional[str] = None
    dietary_style: Optional[str] = None
    food_preferences: Optional[str] = None
    disliked_foods: Optional[str] = None
    meal_schedule: Optional[Any] = None
    water_intake_liters: Optional[float] = None
    activity_level: Optional[str] = None
    stress_level: Optional[int] = None
    sleep_quality: Optional[int] = None
    sleep_hours: Optional[float] = None
    budget_level: Optional[str] = None
    adherence_level: Optional[int] = None
    exercise_frequency_per_week: Optional[int] = None
    exercise_type: Optional[str] = None
    extra_notes: Optional[str] = None
    completed_by_patient: bool = False
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class PatientMetricsOut(BaseModel):
    id: int
    patient_id: int
    weight_kg: Optional[float] = None
    height_cm: Optional[float] = None
    neck_cm: Optional[float] = None
    chest_cm: Optional[float] = None
    waist_cm: Optional[float] = None
    hip_cm: Optional[float] = None
    leg_cm: Optional[float] = None
    calf_cm: Optional[float] = None
    recorded_at: datetime
    source: str
    notes: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PaginatedPatients(BaseModel):
    items: List[PatientOut]
    total: int
    page: int
    page_size: int


class PatientSummaryOut(BaseModel):
    class PatientMini(BaseModel):
        id: int
        full_name: str

    class LatestMetricsMini(BaseModel):
        weight_kg: Optional[float] = None
        height_cm: Optional[float] = None

    class ProfileFlags(BaseModel):
        has_allergies: bool
        has_diseases: bool
        is_profile_complete: bool

    class LatestDietMini(BaseModel):
        id: int
        created_at: datetime
        plan_duration_days: Optional[int] = None

    patient: PatientMini
    latest_metrics: Optional[LatestMetricsMini] = None
    profile_flags: ProfileFlags
    latest_diet: Optional[LatestDietMini] = None


class DoctorMeUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None


class DashboardSummary(BaseModel):
    total_patients: int
    new_patients_30d: int
    incomplete_profiles: int
    diets_generated: int
    latest_activity: List[dict] = Field(default_factory=list)


class PatientProfileUpsert(BaseModel):
    objective: Optional[str] = None
    diseases: Optional[str] = None
    medications: Optional[str] = None
    food_allergies: Optional[str] = None
    foods_avoided: Optional[str] = None
    medical_history: Optional[str] = None
    dietary_style: Optional[str] = None
    food_preferences: Optional[str] = None
    disliked_foods: Optional[str] = None
    meal_schedule: Optional[Any] = None
    water_intake_liters: Optional[float] = None
    activity_level: Optional[str] = None
    stress_level: Optional[int] = None
    sleep_quality: Optional[int] = None
    sleep_hours: Optional[float] = None
    budget_level: Optional[str] = None
    adherence_level: Optional[int] = None
    exercise_frequency_per_week: Optional[int] = None
    exercise_type: Optional[str] = None
    extra_notes: Optional[str] = None


class PatientMetricsCreate(BaseModel):
    weight_kg: Optional[float] = None
    height_cm: Optional[float] = None
    neck_cm: Optional[float] = None
    chest_cm: Optional[float] = None
    waist_cm: Optional[float] = None
    hip_cm: Optional[float] = None
    leg_cm: Optional[float] = None
    calf_cm: Optional[float] = None
    recorded_at: Optional[datetime] = None
    source: Optional[str] = "admin"
    notes: Optional[str] = None


class IntakeLinkCreate(BaseModel):
    patient_id: int
    expires_in_days: int = Field(default=7, ge=1, le=365)
    max_uses: int = Field(default=1, ge=1, le=50)


class IntakeLinkOut(BaseModel):
    id: int
    doctor_id: int
    patient_id: int
    token: str
    status: str
    expires_at: datetime
    max_uses: int
    use_count: int
    last_used_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class IntakeLinkPublicMeta(BaseModel):
    valid: bool
    expires_at: Optional[datetime] = None
    patient_first_name: Optional[str] = None
    patient_last_name: Optional[str] = None
    message: Optional[str] = None


class IntakePublicSubmit(BaseModel):
    first_name: str
    last_name: str
    birth_date: date
    sex: str
    whatsapp: Optional[str] = None
    email: Optional[EmailStr] = None
    country: str
    city: str
    objective: str
    diseases: Optional[str] = None
    medications: Optional[str] = None
    food_allergies: str
    foods_avoided: str
    medical_history: Optional[str] = None
    dietary_style: Optional[str] = None
    food_preferences: Optional[str] = None
    disliked_foods: Optional[str] = None
    meal_schedule: Optional[Any] = None
    water_intake_liters: Optional[float] = None
    stress_level: Optional[int] = None
    sleep_quality: Optional[int] = None
    sleep_hours: Optional[float] = None
    budget_level: Optional[str] = None
    activity_level: Optional[str] = None
    adherence_level: Optional[int] = None
    exercise_frequency_per_week: Optional[int] = None
    exercise_type: Optional[str] = None
    extra_notes: Optional[str] = None
    weight_kg: float
    height_cm: float
    neck_cm: Optional[float] = None
    chest_cm: Optional[float] = None
    waist_cm: Optional[float] = None
    hip_cm: Optional[float] = None
    leg_cm: Optional[float] = None
    calf_cm: Optional[float] = None


class DietGenerateRequest(BaseModel):
    patient_id: int
    doctor_instruction: Optional[str] = None
    duration_days: int = 7
    meals_per_day: Literal[2, 3, 4, 5] = 4
    strategy_mode: Literal["auto", "guided", "manual"] = "auto"
    diet_style: Optional[
        Literal[
            "balanced",
            "low_carb",
            "high_carb",
            "high_protein",
            "mediterranean",
        ]
    ] = None
    macro_mode: Optional["MacroModeRequest"] = None
    manual_targets: Optional["ManualTargetsRequest"] = None

    @field_validator("duration_days")
    @classmethod
    def validate_duration_days(cls, v: int) -> int:
        from app.logic.diet_duration import validate_duration_days as vd

        return vd(v)


class DietRegenerateRequest(BaseModel):
    doctor_instruction: Optional[str] = None
    duration_days: Optional[int] = None
    meals_per_day: Optional[Literal[2, 3, 4, 5]] = None
    strategy_mode: Literal["auto", "guided", "manual"] = "auto"
    diet_style: Optional[
        Literal[
            "balanced",
            "low_carb",
            "high_carb",
            "high_protein",
            "mediterranean",
        ]
    ] = None
    macro_mode: Optional["MacroModeRequest"] = None
    manual_targets: Optional["ManualTargetsRequest"] = None

    @field_validator("duration_days")
    @classmethod
    def validate_duration_opt(cls, v: Optional[int]) -> Optional[int]:
        if v is None:
            return None
        from app.logic.diet_duration import validate_duration_days as vd

        return vd(v)


class TelegramBindingOut(BaseModel):
    linked: bool
    telegram_user_id: Optional[str] = None
    telegram_username: Optional[str] = None
    bot_username: Optional[str] = None


class TelegramBindStartOut(BaseModel):
    deep_link: str
    code: str
    expires_at: datetime


class DietOut(BaseModel):
    id: int
    patient_id: int
    doctor_id: int
    status: str
    title: Optional[str] = None
    summary: Optional[str] = None
    structured_plan_json: Any
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PlanDurationPresetsOut(BaseModel):
    days: List[int]


class DietVersionSummary(BaseModel):
    id: int
    diet_id: int
    version_number: int
    doctor_instruction: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PaginatedDiets(BaseModel):
    items: List[DietOut]
    total: int
    page: int
    page_size: int


class MacroModeRequest(BaseModel):
    protein: Optional[Literal["low", "normal", "high"]] = None
    carbs: Optional[Literal["low", "normal", "high"]] = None
    fat: Optional[Literal["low", "normal", "high"]] = None


class ManualTargetsRequest(BaseModel):
    daily_calories: Optional[float] = Field(None, gt=0)
    protein_g: Optional[float] = Field(None, gt=0)
    carbs_g: Optional[float] = Field(None, gt=0)
    fat_g: Optional[float] = Field(None, gt=0)
