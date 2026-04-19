from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_doctor
from app.core.database import get_db
from app.logic.diet_duration import QUICK_PLAN_DURATION_DAYS
from app.models import Diet, DietVersion, Doctor, Patient, PatientMetrics, PatientProfile
from app.schemas import (
    DietGenerateRequest,
    DietOut,
    DietRegenerateRequest,
    DietVersionSummary,
    PaginatedDiets,
    PlanDurationPresetsOut,
)
from app.services.diet_export import (
    build_diet_export_json_bytes,
    build_diet_export_pdf_bytes,
    build_diet_export_text,
)
from app.services.diet_service import DietGenerationError, create_new_diet, regenerate_diet


router = APIRouter()


@router.get("/duration-presets", response_model=PlanDurationPresetsOut)
async def plan_duration_presets(_doctor: Doctor = Depends(get_current_doctor)):
    """Atajos de duración (días) alineados con Telegram; requiere sesión de doctor."""
    return PlanDurationPresetsOut(days=list(QUICK_PLAN_DURATION_DAYS))


def _http_from_diet_error(e: DietGenerationError) -> HTTPException:
    if e.code == "not_found":
        st = status.HTTP_404_NOT_FOUND
    elif e.code == "openai_config":
        st = status.HTTP_503_SERVICE_UNAVAILABLE
    elif e.code == "openai_error":
        st = status.HTTP_502_BAD_GATEWAY
    else:
        st = status.HTTP_400_BAD_REQUEST
    return HTTPException(
        status_code=st,
        detail={
            "code": e.code,
            "message": e.message,
            "reasons": e.reasons,
        },
    )


@router.get("", response_model=PaginatedDiets)
async def list_diets(
    db: AsyncSession = Depends(get_db),
    doctor: Doctor = Depends(get_current_doctor),
    patient_id: Optional[int] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    conditions = [Diet.doctor_id == doctor.id]
    if patient_id is not None:
        conditions.append(Diet.patient_id == patient_id)
    if status_filter:
        conditions.append(Diet.status == status_filter)

    count_stmt = select(func.count()).select_from(Diet).where(*conditions)
    total = (await db.execute(count_stmt)).scalar_one()
    stmt = (
        select(Diet)
        .where(*conditions)
        .order_by(Diet.updated_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(stmt)
    items = result.scalars().all()
    return PaginatedDiets(
        items=[DietOut.model_validate(d) for d in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/generate", response_model=DietOut, status_code=status.HTTP_201_CREATED)
async def generate_diet(
    body: DietGenerateRequest,
    db: AsyncSession = Depends(get_db),
    doctor: Doctor = Depends(get_current_doctor),
):
    try:
        diet = await create_new_diet(
            db,
            doctor,
            body.patient_id,
            body.doctor_instruction,
            duration_days=body.duration_days,
            meals_per_day=body.meals_per_day,
            strategy_mode=body.strategy_mode,
            diet_style=body.diet_style,
            macro_mode=body.macro_mode.model_dump(exclude_none=True)
            if body.macro_mode
            else None,
            manual_targets=body.manual_targets.model_dump(exclude_none=True)
            if body.manual_targets
            else None,
        )
        await db.commit()
        await db.refresh(diet)
        return diet
    except DietGenerationError as e:
        await db.rollback()
        raise _http_from_diet_error(e) from e


@router.get("/{diet_id}", response_model=DietOut)
async def get_diet(
    diet_id: int,
    db: AsyncSession = Depends(get_db),
    doctor: Doctor = Depends(get_current_doctor),
):
    diet = await db.get(Diet, diet_id)
    if diet is None or diet.doctor_id != doctor.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Diet not found")
    return diet


@router.get("/{diet_id}/versions", response_model=list[DietVersionSummary])
async def list_versions(
    diet_id: int,
    db: AsyncSession = Depends(get_db),
    doctor: Doctor = Depends(get_current_doctor),
):
    diet = await db.get(Diet, diet_id)
    if diet is None or diet.doctor_id != doctor.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Diet not found")
    result = await db.execute(
        select(DietVersion)
        .where(DietVersion.diet_id == diet_id)
        .order_by(DietVersion.version_number.asc())
    )
    rows = result.scalars().all()
    return [DietVersionSummary.model_validate(v) for v in rows]


@router.post("/{diet_id}/regenerate", response_model=DietOut)
async def regenerate_diet_route(
    diet_id: int,
    body: DietRegenerateRequest,
    db: AsyncSession = Depends(get_db),
    doctor: Doctor = Depends(get_current_doctor),
):
    try:
        diet = await regenerate_diet(
            db,
            doctor,
            diet_id,
            body.doctor_instruction,
            duration_days=body.duration_days,
            meals_per_day=body.meals_per_day,
            strategy_mode=body.strategy_mode,
            diet_style=body.diet_style,
            macro_mode=body.macro_mode.model_dump(exclude_none=True)
            if body.macro_mode
            else None,
            manual_targets=body.manual_targets.model_dump(exclude_none=True)
            if body.manual_targets
            else None,
        )
        await db.commit()
        await db.refresh(diet)
        return diet
    except DietGenerationError as e:
        await db.rollback()
        raise _http_from_diet_error(e) from e


@router.get("/{diet_id}/export")
async def export_diet(
    diet_id: int,
    db: AsyncSession = Depends(get_db),
    doctor: Doctor = Depends(get_current_doctor),
    export_format: Literal["txt", "json"] = Query("txt", alias="format"),
):
    diet = await db.get(Diet, diet_id)
    if diet is None or diet.doctor_id != doctor.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Diet not found")
    if export_format == "json":
        body = build_diet_export_json_bytes(diet)
        return Response(
            content=body,
            media_type="application/json; charset=utf-8",
            headers={
                "Content-Disposition": f'attachment; filename="diet_{diet_id}.json"'
            },
        )
    patient = await db.get(Patient, diet.patient_id)
    if patient is not None and patient.doctor_id != doctor.id:
        patient = None
    text = build_diet_export_text(diet, patient=patient)
    return Response(
        content=text.encode("utf-8"),
        media_type="text/plain; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="diet_{diet_id}.txt"'
        },
    )


@router.get("/{diet_id}/pdf")
async def get_diet_pdf(
    diet_id: int,
    db: AsyncSession = Depends(get_db),
    doctor: Doctor = Depends(get_current_doctor),
):
    diet = await db.get(Diet, diet_id)
    if diet is None or diet.doctor_id != doctor.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Diet not found")
    patient = await db.get(Patient, diet.patient_id)
    profile = None
    metrics = None
    if patient is not None and patient.doctor_id == doctor.id:
        pr = await db.execute(
            select(PatientProfile).where(PatientProfile.patient_id == patient.id)
        )
        profile = pr.scalar_one_or_none()
        mr = await db.execute(
            select(PatientMetrics)
            .where(PatientMetrics.patient_id == patient.id)
            .order_by(PatientMetrics.recorded_at.desc())
            .limit(1)
        )
        metrics = mr.scalar_one_or_none()
    pdf_bytes = build_diet_export_pdf_bytes(
        diet,
        patient=patient if patient and patient.doctor_id == doctor.id else None,
        profile=profile,
        metrics=metrics,
        doctor=doctor,
    )
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="diet_{diet_id}.pdf"'
        },
    )
