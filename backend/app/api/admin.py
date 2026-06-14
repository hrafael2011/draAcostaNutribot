from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_admin
from app.core.database import get_db
from app.core.security import get_password_hash
from app.models import Doctor, utcnow
from app.schemas import (
    AdminDoctorCreate,
    AdminDoctorUpdate,
    AdminPasswordReset,
    DoctorOut,
)

router = APIRouter()


# ---------------------------------------------------------------------------
# ⚠️  TEMPORARY ENDPOINT — remove after the initial admin account is created.
# ---------------------------------------------------------------------------

class _SetupAdminRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str


@router.post("/setup", status_code=status.HTTP_201_CREATED)
async def setup_initial_admin(
    body: _SetupAdminRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    One-time bootstrap endpoint: creates the first admin account.
    Rejected with 409 if any admin user already exists, so it is safe to
    leave deployed briefly — it cannot be used to overwrite an existing admin.

    ⚠️  Remove this endpoint once the initial admin has been created.
    """
    # Block if an admin already exists — prevents misuse after initial setup.
    existing = await db.execute(
        select(func.count()).select_from(Doctor).where(Doctor.role == "admin")
    )
    if existing.scalar_one() > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An admin account already exists. Remove this endpoint.",
        )

    doctor = Doctor(
        full_name=body.full_name.strip(),
        email=body.email.lower().strip(),
        hashed_password=get_password_hash(body.password),
        role="admin",
        is_active=True,
        must_change_password=False,
    )
    db.add(doctor)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered.",
        )
    await db.refresh(doctor)
    return {
        "message": "Admin account created successfully. Remove /api/admin/setup now.",
        "id": doctor.id,
        "email": doctor.email,
        "full_name": doctor.full_name,
        "role": doctor.role,
    }


# ---------------------------------------------------------------------------
# End of temporary endpoint
# ---------------------------------------------------------------------------


@router.get("/doctors", response_model=list[DoctorOut])
async def list_doctors(
    db: AsyncSession = Depends(get_db),
    _admin: Doctor = Depends(get_current_admin),
):
    result = await db.execute(select(Doctor).order_by(Doctor.created_at.desc()))
    return result.scalars().all()


@router.post(
    "/doctors",
    response_model=DoctorOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_doctor(
    body: AdminDoctorCreate,
    db: AsyncSession = Depends(get_db),
    _admin: Doctor = Depends(get_current_admin),
):
    doctor = Doctor(
        full_name=body.full_name.strip(),
        email=body.email.lower().strip(),
        phone=body.phone,
        hashed_password=get_password_hash(body.temporary_password),
        role=body.role,
        must_change_password=True,
        is_active=True,
    )
    db.add(doctor)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    await db.refresh(doctor)
    return doctor


@router.patch("/doctors/{doctor_id}", response_model=DoctorOut)
async def update_doctor(
    doctor_id: int,
    body: AdminDoctorUpdate,
    db: AsyncSession = Depends(get_db),
    admin: Doctor = Depends(get_current_admin),
):
    doctor = await _get_doctor(db, doctor_id)
    data = body.model_dump(exclude_unset=True)
    if doctor.id == admin.id and data.get("is_active") is False:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admin cannot deactivate their own account",
        )
    if doctor.id == admin.id and data.get("role") == "doctor":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admin cannot remove their own admin role",
        )
    if "email" in data and data["email"] is not None:
        data["email"] = str(data["email"]).lower().strip()
    if "full_name" in data and data["full_name"] is not None:
        data["full_name"] = data["full_name"].strip()
    for key, value in data.items():
        setattr(doctor, key, value)
    doctor.updated_at = utcnow()
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    await db.refresh(doctor)
    return doctor


@router.post("/doctors/{doctor_id}/reset-password", response_model=DoctorOut)
async def reset_doctor_password(
    doctor_id: int,
    body: AdminPasswordReset,
    db: AsyncSession = Depends(get_db),
    _admin: Doctor = Depends(get_current_admin),
):
    doctor = await _get_doctor(db, doctor_id)
    doctor.hashed_password = get_password_hash(body.temporary_password)
    doctor.must_change_password = True
    doctor.updated_at = utcnow()
    await db.commit()
    await db.refresh(doctor)
    return doctor


async def _get_doctor(db: AsyncSession, doctor_id: int) -> Doctor:
    doctor = await db.get(Doctor, doctor_id)
    if doctor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor not found",
        )
    return doctor
