from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import create_access_token, get_password_hash, verify_password
from app.core.config import settings
from app.api.deps import get_current_active_doctor
from app.models import Doctor, utcnow
from app.schemas import DoctorCreate, DoctorOut, PasswordChange, Token

router = APIRouter()


@router.get("/registration-open")
async def registration_open(db: AsyncSession = Depends(get_db)):
    if settings.is_production:
        return {"open": False}
    count = (
        await db.execute(select(func.count()).select_from(Doctor))
    ).scalar_one()
    return {"open": count == 0}


@router.post("/register", response_model=DoctorOut, status_code=status.HTTP_201_CREATED)
async def register_doctor(body: DoctorCreate, db: AsyncSession = Depends(get_db)):
    if settings.is_production:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Public registration is disabled.",
        )
    existing = (
        await db.execute(select(func.count()).select_from(Doctor))
    ).scalar_one()
    if existing > 0:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Registration is closed: a doctor account already exists.",
        )
    doctor = Doctor(
        full_name=body.full_name,
        email=body.email.lower().strip(),
        phone=body.phone,
        hashed_password=get_password_hash(body.password),
        role="doctor",
        must_change_password=False,
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


@router.post("/token", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Doctor).where(Doctor.email == form_data.username.lower().strip())
    )
    doctor = result.scalar_one_or_none()
    if doctor is None or not verify_password(form_data.password, doctor.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    if not doctor.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive account",
        )
    role = doctor.role or "doctor"
    must_change_password = bool(doctor.must_change_password)
    token = create_access_token(
        str(doctor.id),
        {
            "role": role,
            "must_change_password": must_change_password,
        },
    )
    return Token(
        access_token=token,
        role=role,
        must_change_password=must_change_password,
    )


@router.post("/change-password", response_model=Token)
async def change_password(
    body: PasswordChange,
    doctor: Doctor = Depends(get_current_active_doctor),
    db: AsyncSession = Depends(get_db),
):
    if not verify_password(body.current_password, doctor.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )
    if verify_password(body.new_password, doctor.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be different from the current password",
        )
    doctor.hashed_password = get_password_hash(body.new_password)
    doctor.must_change_password = False
    doctor.updated_at = utcnow()
    await db.commit()
    await db.refresh(doctor)
    role = doctor.role or "doctor"
    token = create_access_token(
        str(doctor.id),
        {
            "role": role,
            "must_change_password": False,
        },
    )
    return Token(access_token=token, role=role, must_change_password=False)


@router.post("/refresh")
async def refresh():
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Refresh tokens are not implemented yet",
    )


@router.post("/logout")
async def logout():
    return {"ok": True}
