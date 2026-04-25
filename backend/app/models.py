from datetime import datetime, timezone
from sqlalchemy import (
    BigInteger,
    Column,
    Integer,
    String,
    Boolean,
    Date,
    DateTime,
    Text,
    ForeignKey,
    Numeric,
    JSON,
)
from sqlalchemy.orm import relationship
from app.core.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Doctor(Base):
    __tablename__ = "doctors"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(160), nullable=False)
    email = Column(String(190), unique=True, index=True, nullable=False)
    phone = Column(String(30), nullable=True)
    hashed_password = Column(String(255), nullable=False)
    telegram_user_id = Column(String(40), unique=True, nullable=True)
    telegram_username = Column(String(120), nullable=True)
    role = Column(String(20), default="doctor", nullable=False)
    must_change_password = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    patients = relationship("Patient", back_populates="doctor", cascade="all, delete")
    intake_links = relationship(
        "PatientIntakeLink", back_populates="doctor", cascade="all, delete"
    )
    diets = relationship("Diet", back_populates="doctor", cascade="all, delete")
    bindings = relationship(
        "DoctorTelegramBinding", back_populates="doctor", cascade="all, delete"
    )


class TelegramPendingLink(Base):
    __tablename__ = "telegram_pending_links"

    id = Column(Integer, primary_key=True, index=True)
    doctor_id = Column(
        Integer, ForeignKey("doctors.id"), nullable=False, unique=True, index=True
    )
    code = Column(String(32), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)


class TelegramProcessedUpdate(Base):
    """Telegram webhook delivery idempotency (one row per update_id)."""

    __tablename__ = "telegram_processed_updates"

    id = Column(Integer, primary_key=True, index=True)
    update_id = Column(BigInteger, unique=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)


class DoctorTelegramBinding(Base):
    __tablename__ = "doctor_telegram_bindings"

    id = Column(Integer, primary_key=True, index=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False)
    telegram_user_id = Column(String(40), unique=True, nullable=False)
    telegram_chat_id = Column(String(40), unique=True, nullable=False)
    telegram_username = Column(String(120), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    doctor = relationship("Doctor", back_populates="bindings")


class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False)
    first_name = Column(String(120), nullable=False)
    last_name = Column(String(120), nullable=False)
    birth_date = Column(Date, nullable=True)
    sex = Column(String(20), nullable=True)
    whatsapp = Column(String(30), nullable=True)
    email = Column(String(190), nullable=True)
    country = Column(String(120), nullable=True)
    city = Column(String(120), nullable=True)
    source = Column(String(20), nullable=False, default="admin")
    is_active = Column(Boolean, default=True, nullable=False)
    is_archived = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    doctor = relationship("Doctor", back_populates="patients")
    profile = relationship(
        "PatientProfile", back_populates="patient", uselist=False, cascade="all, delete"
    )
    metrics = relationship(
        "PatientMetrics", back_populates="patient", cascade="all, delete"
    )
    diets = relationship("Diet", back_populates="patient", cascade="all, delete")
    intake_links = relationship(
        "PatientIntakeLink", back_populates="patient", cascade="all, delete"
    )


class PatientProfile(Base):
    __tablename__ = "patient_profiles"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), unique=True, nullable=False)
    objective = Column(String(80), nullable=True)
    diseases = Column(Text, nullable=True)
    medications = Column(Text, nullable=True)
    food_allergies = Column(Text, nullable=True)
    foods_avoided = Column(Text, nullable=True)
    medical_history = Column(Text, nullable=True)
    dietary_style = Column(String(80), nullable=True)
    food_preferences = Column(Text, nullable=True)
    disliked_foods = Column(Text, nullable=True)
    meal_schedule = Column(JSON, nullable=True)
    water_intake_liters = Column(Numeric(5, 2), nullable=True)
    activity_level = Column(Text, nullable=True)
    stress_level = Column(Integer, nullable=True)
    sleep_quality = Column(Integer, nullable=True)
    sleep_hours = Column(Numeric(4, 2), nullable=True)
    budget_level = Column(Text, nullable=True)
    adherence_level = Column(Integer, nullable=True)
    exercise_frequency_per_week = Column(Integer, nullable=True)
    exercise_type = Column(Text, nullable=True)
    extra_notes = Column(Text, nullable=True)
    completed_by_patient = Column(Boolean, default=False, nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    patient = relationship("Patient", back_populates="profile")


class PatientMetrics(Base):
    __tablename__ = "patient_metrics"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    weight_kg = Column(Numeric(6, 2), nullable=True)
    height_cm = Column(Numeric(6, 2), nullable=True)
    neck_cm = Column(Numeric(6, 2), nullable=True)
    chest_cm = Column(Numeric(6, 2), nullable=True)
    waist_cm = Column(Numeric(6, 2), nullable=True)
    hip_cm = Column(Numeric(6, 2), nullable=True)
    leg_cm = Column(Numeric(6, 2), nullable=True)
    calf_cm = Column(Numeric(6, 2), nullable=True)
    recorded_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    source = Column(String(20), nullable=False, default="admin")
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    patient = relationship("Patient", back_populates="metrics")


class PatientIntakeLink(Base):
    __tablename__ = "patient_intake_links"

    id = Column(Integer, primary_key=True, index=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    token = Column(String(80), unique=True, nullable=False, index=True)
    status = Column(String(20), nullable=False, default="active")
    expires_at = Column(DateTime(timezone=True), nullable=False)
    max_uses = Column(Integer, nullable=False, default=1)
    use_count = Column(Integer, nullable=False, default=0)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    doctor = relationship("Doctor", back_populates="intake_links")
    patient = relationship("Patient", back_populates="intake_links")


class Diet(Base):
    __tablename__ = "diets"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False)
    status = Column(String(20), nullable=False, default="draft")
    title = Column(String(160), nullable=True)
    summary = Column(Text, nullable=True)
    structured_plan_json = Column(JSON, nullable=False, default=dict)
    pdf_file_path = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    patient = relationship("Patient", back_populates="diets")
    doctor = relationship("Doctor", back_populates="diets")
    versions = relationship("DietVersion", back_populates="diet", cascade="all, delete")


class DietVersion(Base):
    __tablename__ = "diet_versions"

    id = Column(Integer, primary_key=True, index=True)
    diet_id = Column(Integer, ForeignKey("diets.id"), nullable=False)
    version_number = Column(Integer, nullable=False)
    doctor_instruction = Column(Text, nullable=True)
    input_snapshot_json = Column(JSON, nullable=False, default=dict)
    output_json = Column(JSON, nullable=False, default=dict)
    pdf_file_path = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    diet = relationship("Diet", back_populates="versions")


class ConversationState(Base):
    __tablename__ = "conversation_states"

    id = Column(Integer, primary_key=True, index=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False)
    channel_user_key = Column(String(80), nullable=False)
    context_data = Column(JSON, nullable=False, default=dict)
    updated_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False)
    action = Column(String(80), nullable=False)
    entity_type = Column(String(80), nullable=False)
    entity_id = Column(Integer, nullable=True)
    payload_json = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
