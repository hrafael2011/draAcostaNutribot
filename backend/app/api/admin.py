from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_admin
from app.core.database import get_db
from app.core.security import get_password_hash
from app.models import AuditLog, Doctor, utcnow
import secrets

from app.schemas import (
    AdminDoctorCreate,
    AdminDoctorCreateResponse,
    AdminDoctorUpdate,
    DoctorOut,
)

router = APIRouter()


@router.get("/doctors", response_model=list[DoctorOut])
async def list_doctors(
    db: AsyncSession = Depends(get_db),
    _admin: Doctor = Depends(get_current_admin),
):
    result = await db.execute(select(Doctor).order_by(Doctor.created_at.desc()))
    return result.scalars().all()


@router.post(
    "/doctors",
    response_model=AdminDoctorCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_doctor(
    body: AdminDoctorCreate,
    db: AsyncSession = Depends(get_db),
    admin: Doctor = Depends(get_current_admin),
):
    # Only super_admin can create admin accounts
    if body.role == "admin" and admin.role != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only super admins can create admin accounts",
        )
    generated_password = secrets.token_urlsafe(12)[:12]
    doctor = Doctor(
        full_name=body.full_name.strip(),
        email=body.email.lower().strip(),
        phone=body.phone,
        hashed_password=get_password_hash(generated_password),
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
    await _log_admin_action(db, admin,
        f"Creó el usuario {doctor.full_name} ({doctor.role})",
        doctor, {"full_name": doctor.full_name, "email": doctor.email, "role": doctor.role})
    return AdminDoctorCreateResponse(
        id=doctor.id,
        full_name=doctor.full_name,
        email=doctor.email,
        phone=doctor.phone,
        role=doctor.role,
        must_change_password=doctor.must_change_password,
        is_active=doctor.is_active,
        created_at=doctor.created_at,
        generated_password=generated_password,
    )


@router.patch("/doctors/{doctor_id}", response_model=DoctorOut)
async def update_doctor(
    doctor_id: int,
    body: AdminDoctorUpdate,
    db: AsyncSession = Depends(get_db),
    admin: Doctor = Depends(get_current_admin),
):
    doctor = await _get_doctor(db, doctor_id)
    data = body.model_dump(exclude_unset=True)
    # Regular admin cannot promote any user to admin
    if admin.role != "super_admin" and data.get("role") == "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only super admins can create admin accounts",
        )
    # Regular admin cannot modify other admin accounts
    if admin.role != "super_admin" and doctor.role in ("admin", "super_admin") and doctor.id != admin.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only super admins can modify other admin accounts",
        )
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
    # Generate a human-readable action description
    if "is_active" in data:
        action = f"Activó a {doctor.full_name}" if data["is_active"] else f"Desactivó a {doctor.full_name}"
    elif data.keys() == {"full_name"}:
        action = f"Actualizó el nombre de {doctor.full_name}"
    elif data.keys() == {"role"}:
        action = f"Cambió el rol de {doctor.full_name}"
    else:
        action = f"Actualizó datos de {doctor.full_name}"
    changes_str = ", ".join(k.replace("_", " ") for k in data)
    await _log_admin_action(db, admin, action, doctor, {"cambios": changes_str if changes_str else None})
    return doctor


@router.post("/doctors/{doctor_id}/reset-password")
async def reset_doctor_password(
    doctor_id: int,
    db: AsyncSession = Depends(get_db),
    admin: Doctor = Depends(get_current_admin),
):
    doctor = await _get_doctor(db, doctor_id)
    # Regular admin cannot reset passwords of other admin accounts
    if admin.role != "super_admin" and doctor.role in ("admin", "super_admin") and doctor.id != admin.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only super admins can reset passwords of other admin accounts",
        )
    generated_password = secrets.token_urlsafe(12)[:12]
    doctor.hashed_password = get_password_hash(generated_password)
    doctor.must_change_password = True
    doctor.updated_at = utcnow()
    await db.commit()
    await db.refresh(doctor)
    await _log_admin_action(db, admin,
        f"Reseteó la contraseña de {doctor.full_name}",
        doctor)
    return {"generated_password": generated_password}


async def _log_admin_action(db: AsyncSession, admin: Doctor, action: str, target: Doctor, details: dict | None = None):
    """Register an audit log entry for an admin action."""
    log = AuditLog(
        doctor_id=admin.id,
        action=action,
        entity_type="doctor",
        entity_id=target.id,
        payload_json=details or {},
    )
    db.add(log)
    await db.commit()


@router.get("/audit-log")
async def list_audit_logs(
    db: AsyncSession = Depends(get_db),
    admin: Doctor = Depends(get_current_admin),
):
    """Devuelve el historial de acciones de administración (solo gestión de usuarios)."""
    admin_actions = [
        "Creó el usuario", "Actualizó datos de", "Reseteó la contraseña de",
        "Activó a", "Desactivó a",
    ]
    from sqlalchemy import or_
    q = (
        select(AuditLog)
        .where(
            AuditLog.entity_type == "doctor",
            or_(AuditLog.action.like(f"{a}%") for a in admin_actions)
        )
        .order_by(AuditLog.created_at.desc())
        .limit(100)
    )
    # Regular admin sees only their own actions
    if admin.role != "super_admin":
        q = q.where(AuditLog.doctor_id == admin.id)
    result = await db.execute(q)
    logs = result.scalars().all()

    # Enrich with admin and target info
    admin_ids = {l.doctor_id for l in logs}
    admins = {d.id: d for d in (await db.execute(select(Doctor).where(Doctor.id.in_(admin_ids)))).scalars()} if admin_ids else {}
    target_ids = {l.entity_id for l in logs if l.entity_id}
    targets = {d.id: d for d in (await db.execute(select(Doctor).where(Doctor.id.in_(target_ids)))).scalars()} if target_ids else {}

    return [
        {
            "id": log.id,
            "fecha": log.created_at.isoformat(),
            "admin": admins[log.doctor_id].full_name if log.doctor_id in admins else "—",
            "accion": log.action,
            "usuario_afectado": targets[log.entity_id].full_name if log.entity_id in targets else "—",
            "detalle": log.payload_json or {},
        }
        for log in logs
    ]


async def _get_doctor(db: AsyncSession, doctor_id: int) -> Doctor:
    doctor = await db.get(Doctor, doctor_id)
    if doctor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor not found",
        )
    return doctor
