from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_doctor
from app.core.database import get_db
from app.models import Doctor, utcnow
from app.schemas import DoctorMeUpdate, DoctorOut

router = APIRouter()


@router.get("/me", response_model=DoctorOut)
async def get_me(doctor: Doctor = Depends(get_current_doctor)):
    return doctor


@router.patch("/me", response_model=DoctorOut)
async def update_me(
    body: DoctorMeUpdate,
    db: AsyncSession = Depends(get_db),
    doctor: Doctor = Depends(get_current_doctor),
):
    data = body.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(doctor, key, value)
    doctor.updated_at = utcnow()
    await db.commit()
    await db.refresh(doctor)
    return doctor
