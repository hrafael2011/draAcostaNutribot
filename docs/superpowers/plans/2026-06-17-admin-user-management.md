# Admin User Management Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement admin user management with independent portals, forced password change flow, and password recovery via email.

**Architecture:** Extend existing auth system. New `PasswordResetToken` model, 3 new endpoints, modify `/auth/token` to accept portal, auto-generate passwords in admin endpoints. UI reuses existing branding (emerald-600, Dra. Acosta logo, same components).

**Tech Stack:** FastAPI + SQLAlchemy async + JWT/bcrypt (backend), React 19 + Tailwind CSS 4 + Phosphor Icons (frontend), Gmail API (email).

---

## File Inventory

### Backend — Files to Create
- `backend/app/models.py` — Add `PasswordResetToken` model (inline, ~15 lines)

### Backend — Files to Modify
- `backend/app/schemas.py` — Add `ForgotPasswordRequest`, `ResetPasswordRequest`, `VerifyTokenResponse`, `AdminDoctorCreateResponse`
- `backend/app/api/auth.py` — Add 3 endpoints (forgot-password, verify-reset-token, reset-password), add `portal` param to `/token`
- `backend/app/api/admin.py` — Modify `create_doctor` and `reset_doctor_password` to auto-generate password
- `backend/app/services/auth_email_service.py` — **Create** with password reset and welcome email templates

### Frontend — Files to Create
- `frontend/src/pages/AdminLogin.tsx` — Independent admin login at `/admin`
- `frontend/src/pages/ResetPassword.tsx` — Password reset form at `/reset-password?token=xxx`

### Frontend — Files to Modify
- `frontend/src/services/api.ts` — Add `forgotPasswordRequest`, `verifyResetTokenRequest`, `resetPasswordRequest`, update `loginRequest` with portal, update `createAdminDoctor` and `resetAdminDoctorPassword`
- `frontend/src/context/AuthContext.tsx` — Add `forgotPassword`, `resetPassword`, `portal` state
- `frontend/src/pages/Login.tsx` — Add "Olvidé contraseña" link + modal, add `portal=doctor`
- `frontend/src/pages/AdminUsers.tsx` — Auto-generate password, redesign with modals, use Button/Badge components
- `frontend/src/components/RequireAuth.tsx` — Add admin route validation
- `frontend/src/App.tsx` — Add `/admin` and `/reset-password` routes
- `frontend/src/layouts/AdminLayout.tsx` — Admin sidebar (only admin items)

---

### Task 1: Backend — Model + Alembic Migration

**Files:**
- Modify: `backend/app/models.py` (add PasswordResetToken)
- Create: `backend/alembic/versions/xxxx_password_reset_tokens.py`

- [ ] **Step 1: Add PasswordResetToken model to models.py**

Append to `backend/app/models.py` (before the closing of the file, after `AuditLog`):

```python
class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id = Column(Integer, primary_key=True, index=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False, index=True)
    token = Column(String(64), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    doctor = relationship("Doctor")
```

- [ ] **Step 2: Generate and run Alembic migration**

Run:
```bash
cd backend && alembic revision --autogenerate -m "add_password_reset_tokens"
# Then:
cd backend && alembic upgrade head
```

Expected: Migration generates a new file in `alembic/versions/` with `password_reset_tokens` table. `alembic upgrade head` completes without errors.

- [ ] **Step 3: Commit**

```bash
git add backend/app/models.py backend/alembic/versions/
git commit -m "feat: add PasswordResetToken model and migration"
```

---

### Task 2: Backend — New Auth Schemas

**Files:**
- Modify: `backend/app/schemas.py`

- [ ] **Step 1: Add new schemas before `Token` class**

Add to `backend/app/schemas.py` (after the existing imports, before `class Token`):

```python
class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=8, max_length=128)


class VerifyTokenResponse(BaseModel):
    valid: bool
    email: Optional[str] = None


class AdminDoctorCreateResponse(DoctorOut):
    generated_password: str


# Add created_at to DoctorOut for the admin table
# Change the existing DoctorOut to include created_at:
#
# class DoctorOut(BaseModel):
#     id: int
#     full_name: str
#     email: EmailStr
#     phone: Optional[str] = None
#     role: str = "doctor"
#     must_change_password: bool = False
#     is_active: bool
#     created_at: Optional[datetime] = None     # <-- add this line
#
#     model_config = ConfigDict(from_attributes=True)
```

- [ ] **Step 2: Verify the file compiles**

Run:
```bash
cd backend && python -c "from app.schemas import ForgotPasswordRequest, ResetPasswordRequest, VerifyTokenResponse, AdminDoctorCreateResponse; print('OK')"
```

Expected: `OK` printed without errors.

- [ ] **Step 3: Commit**

```bash
git add backend/app/schemas.py
git commit -m "feat: add auth schemas for password recovery"
```

---

### Task 3: Backend — Auth Email Templates

**Files:**
- Create: `backend/app/services/auth_email_service.py`
- Modify: `backend/app/services/__init__.py` (add import if needed — empty __init__ is fine)

- [ ] **Step 1: Create auth_email_service.py**

Create `backend/app/services/auth_email_service.py`:

```python
import base64
import logging
from pathlib import Path

from app.services.email_service import send_email_sync
from app.core.config import settings

logger = logging.getLogger(__name__)

_LOGO_B64: str | None = None


def _get_logo_b64() -> str:
    global _LOGO_B64
    if _LOGO_B64 is None:
        logo_path = (
            Path(__file__).resolve().parent.parent.parent.parent
            / "frontend" / "public" / "logo-doctora.jpeg"
        )
        if logo_path.exists():
            _LOGO_B64 = base64.b64encode(logo_path.read_bytes()).decode()
        else:
            _LOGO_B64 = ""
    return _LOGO_B64


def _base_html(content_html: str) -> str:
    logo_src = _get_logo_b64()
    logo_tag = (
        f'<img src="data:image/jpeg;base64,{logo_src}" alt="Dra. Acosta" '
        f'style="height:80px;width:auto;margin-bottom:12px;border-radius:12px;" />'
    ) if logo_src else ""
    return f"""<!DOCTYPE html>
<html><body style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;padding:20px;background:#f8fafc;">
  <div style="background:#fff;border-radius:16px;padding:32px;box-shadow:0 1px 3px rgba(0,0,0,0.08);">
    <div style="text-align:center;margin-bottom:24px;">
      {logo_tag}
      <h1 style="color:#065f46;font-size:22px;margin:0 0 4px 0;">Dra. Acosta</h1>
      <p style="color:#64748b;font-size:14px;margin:0;">Plan Nutricional Personalizado</p>
    </div>
    {content_html}
    <hr style="border:none;border-top:1px solid #e2e8f0;margin:24px 0;" />
    <p style="color:#94a3b8;font-size:11px;text-align:center;margin:0;">
      Dra. Acosta · Nutrición Personalizada · Este es un mensaje automático
    </p>
  </div>
</body></html>"""


def send_password_reset_email(to_email: str, full_name: str, reset_link: str) -> bool:
    content = f"""
    <h2 style="color:#0f172a;font-size:18px;">Hola {full_name},</h2>
    <p style="color:#475569;font-size:14px;line-height:1.6;">
      Recibimos una solicitud para restablecer la contraseña de tu cuenta en <b>Diet Agent</b>.
    </p>
    <div style="text-align:center;margin:28px 0;">
      <a href="{reset_link}" style="background:#10b981;color:#fff;text-decoration:none;padding:14px 32px;border-radius:999px;font-size:15px;font-weight:600;display:inline-block;">
        Restablecer Contraseña
      </a>
    </div>
    <p style="color:#94a3b8;font-size:12px;text-align:center;margin:0;">
      Este enlace expira en <b>30 minutos</b>. Si no solicitaste este cambio, ignora este mensaje.
    </p>
    <p style="color:#94a3b8;font-size:11px;text-align:center;margin-top:16px;">
      Si el botón no funciona, copia este enlace en tu navegador:<br>
      <span style="color:#3b82f6;">{reset_link}</span>
    </p>
    """
    html = _base_html(content)
    return send_email_sync(to_email, "Recuperación de Contraseña — Dra. Acosta", html)


def send_welcome_email(to_email: str, full_name: str, temp_password: str, login_link: str) -> bool:
    content = f"""
    <h2 style="color:#0f172a;font-size:18px;">¡Bienvenido(a) a Diet Agent, {full_name}!</h2>
    <p style="color:#475569;font-size:14px;line-height:1.6;">
      Se ha creado una cuenta para ti en el sistema de gestión nutricional.
    </p>
    <p style="color:#475569;font-size:14px;line-height:1.8;">
      <b>Email:</b> {to_email}<br>
      <b>Contraseña temporal:</b>
      <code style="background:#fefce8;padding:4px 8px;border-radius:4px;font-size:14px;">{temp_password}</code>
    </p>
    <p style="color:#ef4444;font-size:13px;">
      ⚠️ Al iniciar sesión por primera vez, deberás cambiar esta contraseña.
    </p>
    <div style="text-align:center;margin:28px 0;">
      <a href="{login_link}" style="background:#10b981;color:#fff;text-decoration:none;padding:14px 32px;border-radius:999px;font-size:15px;font-weight:600;display:inline-block;">
        Iniciar Sesión
      </a>
    </div>
    """
    html = _base_html(content)
    return send_email_sync(to_email, "Bienvenido a Nutribot — Dra. Acosta", html)
```

- [ ] **Step 2: Verify the file can be imported**

Run:
```bash
cd backend && python -c "from app.services.auth_email_service import send_password_reset_email, send_welcome_email; print('OK')"
```

Expected: `OK` printed without errors.

- [ ] **Step 3: Commit**

```bash
git add backend/app/services/auth_email_service.py
git commit -m "feat: add password reset and welcome email templates"
```

---

### Task 4: Backend — Auth Endpoints (Forgot, Verify, Reset)

**Files:**
- Modify: `backend/app/api/auth.py`
- Modify: `backend/app/schemas.py` (already done in Task 2)

- [ ] **Step 1: Add forgot-password, verify-reset-token, reset-password endpoints**

Add these imports to `backend/app/api/auth.py` (top of file):
```python
import secrets
from datetime import timedelta
from app.models import PasswordResetToken
from app.schemas import ForgotPasswordRequest, ResetPasswordRequest, VerifyTokenResponse
from app.services.auth_email_service import send_password_reset_email
from app.core.config import settings
```

Add these new endpoints after the existing `@router.post("/logout")` in `backend/app/api/auth.py`:

```python
@router.post("/forgot-password")
async def forgot_password(
    body: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    # Always respond same way regardless of whether email exists (prevents enumeration)
    result = await db.execute(
        select(Doctor).where(Doctor.email == body.email.lower().strip())
    )
    doctor = result.scalar_one_or_none()

    if doctor is not None:
        # Invalidate any existing unused tokens for this doctor
        existing = await db.execute(
            select(PasswordResetToken).where(
                PasswordResetToken.doctor_id == doctor.id,
                PasswordResetToken.used == False,
                PasswordResetToken.expires_at > utcnow(),
            )
        )
        for tok in existing.scalars():
            tok.used = True

        token = secrets.token_urlsafe(32)
        reset_token = PasswordResetToken(
            doctor_id=doctor.id,
            token=token,
            expires_at=utcnow() + timedelta(minutes=30),
        )
        db.add(reset_token)
        await db.commit()

        reset_link = f"{settings.APP_URL}/reset-password?token={token}"
        send_password_reset_email(doctor.email, doctor.full_name, reset_link)

    return {"ok": True, "message": "Si el correo existe, recibirás instrucciones"}


@router.get("/verify-reset-token", response_model=VerifyTokenResponse)
async def verify_reset_token(
    token: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(PasswordResetToken).where(PasswordResetToken.token == token)
    )
    reset_token = result.scalar_one_or_none()

    if reset_token is None or reset_token.used or reset_token.expires_at <= utcnow():
        return VerifyTokenResponse(valid=False)

    doctor = await db.get(Doctor, reset_token.doctor_id)
    if doctor is None or not doctor.is_active:
        return VerifyTokenResponse(valid=False)

    return VerifyTokenResponse(valid=True, email=doctor.email)


@router.post("/reset-password")
async def reset_password(
    body: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(PasswordResetToken).where(PasswordResetToken.token == body.token)
    )
    reset_token = result.scalar_one_or_none()

    if reset_token is None or reset_token.used or reset_token.expires_at <= utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token inválido o expirado",
        )

    doctor = await db.get(Doctor, reset_token.doctor_id)
    if doctor is None or not doctor.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token inválido o expirado",
        )

    doctor.hashed_password = get_password_hash(body.new_password)
    doctor.must_change_password = False
    doctor.updated_at = utcnow()
    reset_token.used = True
    await db.commit()

    return {"ok": True}
```

- [ ] **Step 2: Test that the endpoints load**

Run:
```bash
cd backend && python -c "from app.api.auth import router; print('OK:', [r.path for r in router.routes])"
```

Expected: Output includes `forgot-password`, `verify-reset-token`, `reset-password`.

- [ ] **Step 3: Commit**

```bash
git add backend/app/api/auth.py
git commit -m "feat: add forgot-password, verify-reset-token, reset-password endpoints"
```

---

### Task 5: Backend — Modify /auth/token to accept portal

**Files:**
- Modify: `backend/app/api/auth.py`

- [ ] **Step 1: Add portal validation to POST /auth/token**

In `backend/app/api/auth.py`, replace the `login` function with:

```python
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

    # Portal validation
    portal = form_data.client_secret or "doctor"
    if portal == "admin" and doctor.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access restricted to administrators",
        )
    if portal == "doctor" and doctor.role != "doctor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access restricted to doctors",
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
```

**Note:** OAuth2PasswordRequestForm has `client_secret` field we repurpose as `portal`. The frontend will pass `portal` as the `client_secret` field in the form body. This avoids changing the form structure while adding portal support.

- [ ] **Step 2: Verify the endpoint still works for existing flow**

Run:
```bash
cd backend && python -c "
from app.api.auth import router
login_route = [r for r in router.routes if r.path == '/token'][0]
print('Token endpoint OK, portal validation added')
"
```

Expected: Prints confirmation message.

- [ ] **Step 3: Commit**

```bash
git add backend/app/api/auth.py
git commit -m "feat: add portal validation to auth/token endpoint"
```

---

### Task 6: Backend — Auto-generate passwords in Admin endpoints

**Files:**
- Modify: `backend/app/api/admin.py`

- [ ] **Step 1: Modify create_doctor to auto-generate password**

Add import at top of `backend/app/api/admin.py`:
```python
import secrets
from app.schemas import AdminDoctorCreateResponse
```

Replace `create_doctor` function:

```python
@router.post(
    "/doctors",
    response_model=AdminDoctorCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_doctor(
    body: AdminDoctorCreate,
    db: AsyncSession = Depends(get_db),
    _admin: Doctor = Depends(get_current_admin),
):
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
    return AdminDoctorCreateResponse(
        id=doctor.id,
        full_name=doctor.full_name,
        email=doctor.email,
        phone=doctor.phone,
        role=doctor.role,
        must_change_password=doctor.must_change_password,
        is_active=doctor.is_active,
        generated_password=generated_password,
    )
```

- [ ] **Step 2: Modify reset-password to auto-generate**

Remove the `body: AdminPasswordReset` parameter and auto-generate:

```python
@router.post("/doctors/{doctor_id}/reset-password")
async def reset_doctor_password(
    doctor_id: int,
    db: AsyncSession = Depends(get_db),
    _admin: Doctor = Depends(get_current_admin),
):
    doctor = await _get_doctor(db, doctor_id)
    generated_password = secrets.token_urlsafe(12)[:12]
    doctor.hashed_password = get_password_hash(generated_password)
    doctor.must_change_password = True
    doctor.updated_at = utcnow()
    await db.commit()
    await db.refresh(doctor)
    return {"generated_password": generated_password}
```

- [ ] **Step 3: Verify the admin module loads**

Run:
```bash
cd backend && python -c "from app.api.admin import router; print('OK:', len(router.routes), 'routes')"
```

Expected: `OK: 4 routes` printed.

- [ ] **Step 4: Commit**

```bash
git add backend/app/api/admin.py
git commit -m "feat: auto-generate passwords in admin endpoints"
```

---

### Task 7: Frontend — API service functions

**Files:**
- Modify: `frontend/src/services/api.ts`

- [ ] **Step 1: Add new API functions**

Add to `frontend/src/services/api.ts` after the existing `resetAdminDoctorPassword` function:

```typescript
export async function forgotPasswordRequest(email: string) {
  const res = await fetch(`${API_BASE_URL}/auth/forgot-password`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email }),
  })
  return parseJson<{ ok: boolean; message: string }>(res)
}

export async function verifyResetTokenRequest(token: string) {
  const res = await fetch(
    `${API_BASE_URL}/auth/verify-reset-token?token=${encodeURIComponent(token)}`,
  )
  return parseJson<{ valid: boolean; email?: string }>(res)
}

export async function resetPasswordRequest(token: string, newPassword: string) {
  const res = await fetch(`${API_BASE_URL}/auth/reset-password`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ token, new_password: newPassword }),
  })
  if (!res.ok) {
    throw new Error(await readApiError(res) || "Error al restablecer la contraseña")
  }
  return parseJson<{ ok: boolean }>(res)
}
```

- [ ] **Step 2: Modify loginRequest to accept portal**

Replace the existing `loginRequest` function:

```typescript
export async function loginRequest(email: string, password: string, portal: "admin" | "doctor" = "doctor") {
  const body = new URLSearchParams()
  body.set("username", email.trim())
  body.set("password", password)
  body.set("client_secret", portal)  // OAuth2PasswordRequestForm's client_secret used as portal
  const res = await fetch(`${API_BASE_URL}/auth/token`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body,
  })
  if (!res.ok) {
    throw new Error(await readApiError(res) || "Login failed")
  }
  const data = (await res.json()) as {
    access_token: string
    role: string
    must_change_password: boolean
  }
  setStoredToken(data.access_token)
  return data
}
```

- [ ] **Step 3: Update createAdminDoctor — remove temporary_password from request**

Replace the existing `createAdminDoctor`:

```typescript
export function createAdminDoctor(body: {
  full_name: string
  email: string
  phone?: string | null
  role: "admin" | "doctor"
}) {
  return authFetch("/admin/doctors", {
    method: "POST",
    body: JSON.stringify(body),
  }).then((r) => parseJson<{ generated_password: string } & DoctorOut>(r))
}
```

- [ ] **Step 4: Update resetAdminDoctorPassword**

Replace the existing function:

```typescript
export function resetAdminDoctorPassword(doctorId: number) {
  return authFetch(`/admin/doctors/${doctorId}/reset-password`, {
    method: "POST",
  }).then((r) => parseJson<{ generated_password: string }>(r))
}
```

- [ ] **Step 5: Verify TypeScript compiles**

Run:
```bash
cd frontend && npx tsc --noEmit 2>&1 | head -30
```

Expected: No errors, or only pre-existing errors unrelated to changes.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/services/api.ts
git commit -m "feat: add password reset API functions and portal support"
```

---

### Task 8: Frontend — AuthContext updates

**Files:**
- Modify: `frontend/src/context/AuthContext.tsx`

- [ ] **Step 1: Add forgotPassword, resetPassword, and portal to AuthContext**

Replace the file contents:

```typescript
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react"
import { setUnauthorizedHandler } from "../services/authBridge"
import {
  changePasswordRequest,
  forgotPasswordRequest,
  getStoredToken,
  loginRequest,
  resetPasswordRequest,
  setStoredToken,
} from "../services/api"

type AuthSession = {
  role: string
  mustChangePassword: boolean
}

type AuthContextValue = {
  token: string | null
  session: AuthSession | null
  portal: "admin" | "doctor" | null
  login: (email: string, password: string, portal?: "admin" | "doctor") => Promise<void>
  changePassword: (currentPassword: string, newPassword: string) => Promise<void>
  forgotPassword: (email: string) => Promise<{ message: string }>
  resetPassword: (token: string, newPassword: string) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(getStoredToken)
  const [portal, setPortal] = useState<"admin" | "doctor" | null>(null)
  const [session, setSession] = useState<AuthSession | null>(() =>
    readSessionFromToken(getStoredToken()),
  )

  useEffect(() => {
    setUnauthorizedHandler(() => {
      setStoredToken(null)
      setToken(null)
      setSession(null)
      setPortal(null)
    })
    return () => setUnauthorizedHandler(null)
  }, [])

  const login = useCallback(async (email: string, password: string, p?: "admin" | "doctor") => {
    const data = await loginRequest(email, password, p)
    const nextToken = getStoredToken()
    setToken(nextToken)
    setPortal(p || "doctor")
    setSession({
      role: data.role || "doctor",
      mustChangePassword: Boolean(data.must_change_password),
    })
  }, [])

  const changePassword = useCallback(
    async (currentPassword: string, newPassword: string) => {
      const data = await changePasswordRequest(currentPassword, newPassword)
      const nextToken = getStoredToken()
      setToken(nextToken)
      setSession({
        role: data.role || "doctor",
        mustChangePassword: Boolean(data.must_change_password),
      })
    },
    [],
  )

  const forgotPassword = useCallback(async (email: string) => {
    return forgotPasswordRequest(email)
  }, [])

  const resetPassword = useCallback(async (token: string, newPassword: string) => {
    await resetPasswordRequest(token, newPassword)
  }, [])

  const logout = useCallback(() => {
    setStoredToken(null)
    setToken(null)
    setSession(null)
    setPortal(null)
  }, [])

  const value = useMemo(
    () => ({ token, session, portal, login, changePassword, forgotPassword, resetPassword, logout }),
    [token, session, portal, login, changePassword, forgotPassword, resetPassword, logout],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

function readSessionFromToken(token: string | null): AuthSession | null {
  if (!token) return null
  try {
    const payload = JSON.parse(decodeBase64Url(token.split(".")[1] || ""))
    return {
      role: typeof payload.role === "string" ? payload.role : "doctor",
      mustChangePassword: Boolean(payload.must_change_password),
    }
  } catch {
    return null
  }
}

function decodeBase64Url(value: string) {
  const base64 = value.replace(/-/g, "+").replace(/_/g, "/")
  const padded = base64.padEnd(base64.length + ((4 - (base64.length % 4)) % 4), "=")
  return atob(padded)
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error("useAuth must be used within AuthProvider")
  return ctx
}
```

- [ ] **Step 2: Verify TypeScript compiles**

Run:
```bash
cd frontend && npx tsc --noEmit 2>&1 | head -30
```

Expected: No new errors. If there are pre-existing errors, note them but don't fix now.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/context/AuthContext.tsx
git commit -m "feat: add forgotPassword, resetPassword, portal to AuthContext"
```

---

### Task 9: Frontend — AdminLogin page

**Files:**
- Create: `frontend/src/pages/AdminLogin.tsx`

- [ ] **Step 1: Create AdminLogin page**

Create `frontend/src/pages/AdminLogin.tsx`:

```tsx
import { useState, type FormEvent } from "react"
import { useNavigate } from "react-router-dom"
import { useAuth } from "../context/AuthContext"
import { Eye, EyeSlash } from "@phosphor-icons/react"
import Button from "../components/ui/Button"

export default function AdminLogin() {
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState("")
  const [loading, setLoading] = useState(false)
  const [forgotOpen, setForgotOpen] = useState(false)
  const [forgotEmail, setForgotEmail] = useState("")
  const [forgotMessage, setForgotMessage] = useState<string | null>(null)
  const [forgotLoading, setForgotLoading] = useState(false)
  const { login, forgotPassword } = useAuth()
  const navigate = useNavigate()

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError("")
    setLoading(true)
    try {
      await login(email, password, "admin")
      navigate("/admin/users", { replace: true })
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al iniciar sesión")
    } finally {
      setLoading(false)
    }
  }

  const handleForgotSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setForgotLoading(true)
    setForgotMessage(null)
    try {
      const result = await forgotPassword(forgotEmail)
      setForgotMessage(result.message)
    } catch {
      setForgotMessage("Si el correo existe, recibirás instrucciones")
    } finally {
      setForgotLoading(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 px-4">
      <div className="w-full max-w-sm">
        <div className="mb-8 text-center">
          <img
            src="/logo-login.png"
            alt="Dra. Acosta Nutribot"
            className="mx-auto mb-4"
            width={180}
            height={174}
          />
          <h1 className="text-xl font-bold text-gray-800">Admin • Dra. Acosta</h1>
          <p className="text-sm text-gray-500">Panel de administración</p>
        </div>

        <form
          onSubmit={handleSubmit}
          className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm"
        >
          {error && (
            <div className="mb-4 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">
              {error}
            </div>
          )}

          <label className="mb-1 block text-sm font-medium text-gray-700">
            Correo electrónico
          </label>
          <input
            type="email"
            required
            autoFocus
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="admin@clinica.com"
            className="mb-4 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm
              focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
          />

          <label className="mb-1 block text-sm font-medium text-gray-700">
            Contraseña
          </label>
          <div className="relative mb-4">
            <input
              type={showPassword ? "text" : "password"}
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 pr-10 text-sm
                focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute right-2.5 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 transition-colors"
              aria-label={showPassword ? "Ocultar contraseña" : "Mostrar contraseña"}
              tabIndex={-1}
            >
              {showPassword ? <EyeSlash size={18} /> : <Eye size={18} />}
            </button>
          </div>

          <Button type="submit" disabled={loading} className="w-full">
            {loading ? "Iniciando sesión..." : "Iniciar sesión"}
          </Button>

          <div className="mt-3 text-center">
            <button
              type="button"
              onClick={() => setForgotOpen(true)}
              className="text-sm text-emerald-600 hover:text-emerald-700 hover:underline"
            >
              ¿Olvidaste tu contraseña?
            </button>
          </div>
        </form>
      </div>

      {/* Forgot password modal */}
      {forgotOpen && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4"
          onClick={() => setForgotOpen(false)}
        >
          <div
            className="w-full max-w-sm rounded-xl bg-white p-6 shadow-lg"
            onClick={(e) => e.stopPropagation()}
          >
            <h2 className="mb-2 text-lg font-bold text-gray-800">
              Recuperar contraseña
            </h2>
            <p className="mb-4 text-sm text-gray-500">
              Ingresa tu correo y te enviaremos un enlace para restablecer tu contraseña.
            </p>
            {forgotMessage ? (
              <>
                <div className="mb-4 rounded-lg bg-emerald-50 px-3 py-2 text-sm text-emerald-700">
                  {forgotMessage}
                </div>
                <Button
                  variant="secondary"
                  onClick={() => { setForgotOpen(false); setForgotMessage(null); }}
                  className="w-full"
                >
                  Cerrar
                </Button>
              </>
            ) : (
              <form onSubmit={handleForgotSubmit}>
                <input
                  type="email"
                  required
                  value={forgotEmail}
                  onChange={(e) => setForgotEmail(e.target.value)}
                  placeholder="admin@clinica.com"
                  className="mb-4 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm
                    focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
                />
                <Button type="submit" disabled={forgotLoading} className="w-full">
                  {forgotLoading ? "Enviando..." : "Enviar enlace"}
                </Button>
              </form>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
```

- [ ] **Step 2: Verify TypeScript compiles**

Run:
```bash
cd frontend && npx tsc --noEmit 2>&1 | head -30
```

Expected: No new errors.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/pages/AdminLogin.tsx
git commit -m "feat: add AdminLogin page at /admin"
```

---

### Task 10: Frontend — Login page modifications (forgot password)

**Files:**
- Modify: `frontend/src/pages/Login.tsx`

- [ ] **Step 1: Add forgot password modal and portal=doctor**

Replace the entire `Login.tsx`:

```tsx
import { useState, type FormEvent } from "react"
import { useNavigate, useLocation } from "react-router-dom"
import { useAuth } from "../context/AuthContext"
import { Eye, EyeSlash } from "@phosphor-icons/react"
import Button from "../components/ui/Button"

export default function Login() {
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState("")
  const [loading, setLoading] = useState(false)
  const [forgotOpen, setForgotOpen] = useState(false)
  const [forgotEmail, setForgotEmail] = useState("")
  const [forgotMessage, setForgotMessage] = useState<string | null>(null)
  const [forgotLoading, setForgotLoading] = useState(false)
  const { login, forgotPassword } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  const from = (location.state as { from?: string })?.from || "/dashboard"

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError("")
    setLoading(true)
    try {
      await login(email, password, "doctor")
      navigate(from, { replace: true })
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al iniciar sesión")
    } finally {
      setLoading(false)
    }
  }

  const handleForgotSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setForgotLoading(true)
    setForgotMessage(null)
    try {
      const result = await forgotPassword(forgotEmail)
      setForgotMessage(result.message)
    } catch {
      setForgotMessage("Si el correo existe, recibirás instrucciones")
    } finally {
      setForgotLoading(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 px-4">
      <div className="w-full max-w-sm">
        <div className="mb-8 text-center">
          <img
            src="/logo-login.png"
            alt="Dra. Acosta Nutribot"
            className="mx-auto mb-4"
            width={180}
            height={174}
          />
          <h1 className="text-xl font-bold text-gray-800">Dra. Acosta</h1>
          <p className="text-sm text-gray-500">Nutribot — Gestión Nutricional</p>
        </div>

        <form
          onSubmit={handleSubmit}
          className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm"
        >
          {error && (
            <div className="mb-4 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">
              {error}
            </div>
          )}

          <label className="mb-1 block text-sm font-medium text-gray-700">
            Correo electrónico
          </label>
          <input
            type="email"
            required
            autoFocus
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="doctora@ejemplo.com"
            className="mb-4 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm
              focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
          />

          <label className="mb-1 block text-sm font-medium text-gray-700">
            Contraseña
          </label>
          <div className="relative mb-4">
            <input
              type={showPassword ? "text" : "password"}
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 pr-10 text-sm
                focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute right-2.5 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 transition-colors"
              aria-label={showPassword ? "Ocultar contraseña" : "Mostrar contraseña"}
              tabIndex={-1}
            >
              {showPassword ? <EyeSlash size={18} /> : <Eye size={18} />}
            </button>
          </div>

          <Button type="submit" disabled={loading} className="w-full">
            {loading ? "Iniciando sesión..." : "Iniciar sesión"}
          </Button>

          <div className="mt-3 text-center">
            <button
              type="button"
              onClick={() => setForgotOpen(true)}
              className="text-sm text-emerald-600 hover:text-emerald-700 hover:underline"
            >
              ¿Olvidaste tu contraseña?
            </button>
          </div>
        </form>
      </div>

      {/* Forgot password modal */}
      {forgotOpen && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4"
          onClick={() => setForgotOpen(false)}
        >
          <div
            className="w-full max-w-sm rounded-xl bg-white p-6 shadow-lg"
            onClick={(e) => e.stopPropagation()}
          >
            <h2 className="mb-2 text-lg font-bold text-gray-800">
              Recuperar contraseña
            </h2>
            <p className="mb-4 text-sm text-gray-500">
              Ingresa tu correo y te enviaremos un enlace para restablecer tu contraseña.
            </p>
            {forgotMessage ? (
              <>
                <div className="mb-4 rounded-lg bg-emerald-50 px-3 py-2 text-sm text-emerald-700">
                  {forgotMessage}
                </div>
                <Button
                  variant="secondary"
                  onClick={() => { setForgotOpen(false); setForgotMessage(null); }}
                  className="w-full"
                >
                  Cerrar
                </Button>
              </>
            ) : (
              <form onSubmit={handleForgotSubmit}>
                <input
                  type="email"
                  required
                  value={forgotEmail}
                  onChange={(e) => setForgotEmail(e.target.value)}
                  placeholder="doctora@ejemplo.com"
                  className="mb-4 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm
                    focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
                />
                <Button type="submit" disabled={forgotLoading} className="w-full">
                  {forgotLoading ? "Enviando..." : "Enviar enlace"}
                </Button>
              </form>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
```

- [ ] **Step 2: Verify TypeScript compiles**

Run:
```bash
cd frontend && npx tsc --noEmit 2>&1 | head -30
```

Expected: No new errors.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/pages/Login.tsx
git commit -m "feat: add forgot password flow to Login page"
```

---

### Task 11: Frontend — ResetPassword page

**Files:**
- Create: `frontend/src/pages/ResetPassword.tsx`

- [ ] **Step 1: Create ResetPassword page**

Create `frontend/src/pages/ResetPassword.tsx`:

```tsx
import { useEffect, useState, type FormEvent } from "react"
import { useNavigate, useSearchParams } from "react-router-dom"
import Button from "../components/ui/Button"

type PageState = "verifying" | "invalid" | "form" | "success" | "error"

export default function ResetPassword() {
  const [searchParams] = useSearchParams()
  const token = searchParams.get("token") || ""
  const navigate = useNavigate()

  const [state, setState] = useState<PageState>("verifying")
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [confirm, setConfirm] = useState("")
  const [errorMsg, setErrorMsg] = useState("")

  useEffect(() => {
    if (!token) {
      setState("invalid")
      return
    }
    const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8002/api"
    fetch(`${API_BASE}/auth/verify-reset-token?token=${encodeURIComponent(token)}`)
      .then((r) => r.json())
      .then((data) => {
        if (data.valid) {
          setEmail(data.email || "")
          setState("form")
        } else {
          setState("invalid")
        }
      })
      .catch(() => setState("invalid"))
  }, [token])

  const isValid =
    password.length >= 8 &&
    /[A-Z]/.test(password) &&
    /[0-9]/.test(password) &&
    password === confirm

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    if (!isValid) return
    setErrorMsg("")
    const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8002/api"
    try {
      const res = await fetch(`${API_BASE}/auth/reset-password`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token, new_password: password }),
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: "Error" }))
        throw new Error(err.detail || "Error al restablecer la contraseña")
      }
      setState("success")
      setTimeout(() => navigate("/login", { replace: true }), 3000)
    } catch (err) {
      setErrorMsg(err instanceof Error ? err.message : "Error al restablecer la contraseña")
      setState("error")
    }
  }

  if (state === "verifying") {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-50 px-4">
        <div className="text-center">
          <div className="mx-auto mb-4 h-8 w-8 animate-spin rounded-full border-4 border-emerald-500 border-t-transparent" />
          <p className="text-gray-500">Verificando enlace...</p>
        </div>
      </div>
    )
  }

  if (state === "invalid") {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-50 px-4">
        <div className="w-full max-w-sm text-center">
          <img src="/logo-login.png" alt="Dra. Acosta" className="mx-auto mb-6" width={120} height={116} />
          <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
            <h1 className="mb-2 text-lg font-bold text-gray-800">Enlace inválido</h1>
            <p className="mb-6 text-sm text-gray-500">
              Este enlace ha expirado o no es válido. Solicita uno nuevo desde la página de inicio de sesión.
            </p>
            <Button onClick={() => navigate("/login")} className="w-full">
              Ir a iniciar sesión
            </Button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 px-4">
      <div className="w-full max-w-sm">
        <div className="mb-8 text-center">
          <img src="/logo-login.png" alt="Dra. Acosta" className="mx-auto mb-4" width={180} height={174} />
          <h1 className="text-xl font-bold text-gray-800">Dra. Acosta</h1>
          <p className="text-sm text-gray-500">Nutribot — Gestión Nutricional</p>
        </div>

        {state === "success" ? (
          <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm text-center">
            <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-emerald-100">
              <span className="text-xl text-emerald-600">✓</span>
            </div>
            <h2 className="mb-2 text-lg font-bold text-gray-800">Contraseña cambiada</h2>
            <p className="text-sm text-gray-500">
              Redirigiendo al inicio de sesión...
            </p>
          </div>
        ) : (
          <form
            onSubmit={handleSubmit}
            className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm"
          >
            <h2 className="mb-1 text-lg font-bold text-gray-800">Restablecer contraseña</h2>
            <p className="mb-4 text-sm text-gray-500">
              {email ? `Para: ${email}` : "Ingresa tu nueva contraseña"}
            </p>

            {errorMsg && (
              <div className="mb-4 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">
                {errorMsg}
              </div>
            )}

            <label className="mb-1 block text-sm font-medium text-gray-700">
              Nueva contraseña
            </label>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Mínimo 8 caracteres"
              className="mb-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm
                focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
            />
            <div className="mb-4 text-xs text-gray-400">
              Mín. 8 caracteres, al menos 1 mayúscula y 1 número
            </div>

            <label className="mb-1 block text-sm font-medium text-gray-700">
              Confirmar nueva contraseña
            </label>
            <input
              type="password"
              required
              value={confirm}
              onChange={(e) => setConfirm(e.target.value)}
              placeholder="Repite la contraseña"
              className="mb-6 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm
                focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
            />

            <Button type="submit" disabled={!isValid} className="w-full">
              Cambiar Contraseña
            </Button>
          </form>
        )}
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Verify TypeScript compiles**

Run:
```bash
cd frontend && npx tsc --noEmit 2>&1 | head -30
```

Expected: No new errors.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/pages/ResetPassword.tsx
git commit -m "feat: add ResetPassword page at /reset-password"
```

---

### Task 12: Frontend — AdminUsers improvements

**Files:**
- Modify: `frontend/src/pages/AdminUsers.tsx`

- [ ] **Step 1: Add `created_at` to DoctorOut in frontend types**

In `frontend/src/types/index.ts`, add `created_at` to the `DoctorOut` type:

```typescript
export type DoctorOut = {
  id: number
  full_name: string
  email: string
  phone?: string | null
  role: string
  must_change_password: boolean
  is_active: boolean
  telegram_user_id?: string | null
  telegram_username?: string | null
  created_at?: string | null      // <-- add this line
}
```

- [ ] **Step 2: Rewrite AdminUsers with auto-generated passwords, modals, and proper UI**

Replace entire `frontend/src/pages/AdminUsers.tsx`:

```tsx
import { FormEvent, useCallback, useEffect, useState } from "react"
import {
  createAdminDoctor,
  getAdminDoctors,
  resetAdminDoctorPassword,
  updateAdminDoctor,
} from "../services/api"
import type { DoctorOut } from "../types"
import Button from "../components/ui/Button"
import Badge from "../components/ui/Badge"
import { Users, Plus, X, Copy, ArrowsClockwise } from "@phosphor-icons/react"

type Role = "admin" | "doctor"

function generatePassword(): string {
  const chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
  let result = ""
  for (let i = 0; i < 10; i++) {
    result += chars.charAt(Math.floor(Math.random() * chars.length))
  }
  // Ensure at least one uppercase and one number
  if (!/[A-Z]/.test(result)) result = "A" + result.slice(1)
  if (!/[0-9]/.test(result)) result = "5" + result.slice(1)
  return result
}

export default function AdminUsers() {
  const [doctors, setDoctors] = useState<DoctorOut[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [message, setMessage] = useState<string | null>(null)

  // Create modal
  const [showCreate, setShowCreate] = useState(false)
  const [createName, setCreateName] = useState("")
  const [createEmail, setCreateEmail] = useState("")
  const [createRole, setCreateRole] = useState<Role>("doctor")
  const [generatedPassword, setGeneratedPassword] = useState(generatePassword())
  const [sendEmail, setSendEmail] = useState(false)
  const [creating, setCreating] = useState(false)

  // Reset modal
  const [resetDoctor, setResetDoctor] = useState<DoctorOut | null>(null)
  const [resetGeneratedPass, setResetGeneratedPass] = useState(generatePassword())
  const [sendResetEmail, setSendResetEmail] = useState(false)
  const [resetting, setResetting] = useState(false)

  const load = useCallback(() => {
    setError(null)
    setLoading(true)
    getAdminDoctors()
      .then(setDoctors)
      .catch((err) =>
        setError(err instanceof Error ? err.message : "No se pudieron cargar usuarios."),
      )
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => { load() }, [load])

  // Create user
  async function onCreate(e: FormEvent) {
    e.preventDefault()
    setError(null)
    setCreating(true)
    try {
      const result = await createAdminDoctor({
        full_name: createName,
        email: createEmail,
        role: createRole,
      })
      setMessage(`Usuario creado. Contraseña: ${result.generated_password}`)
      setShowCreate(false)
      resetCreateForm()
      load()
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo crear el usuario.")
    } finally {
      setCreating(false)
    }
  }

  function resetCreateForm() {
    setCreateName("")
    setCreateEmail("")
    setCreateRole("doctor")
    setGeneratedPassword(generatePassword())
    setSendEmail(false)
  }

  // Reset password
  async function onResetPassword(e: FormEvent) {
    e.preventDefault()
    if (!resetDoctor) return
    setError(null)
    setResetting(true)
    try {
      const result = await resetAdminDoctorPassword(resetDoctor.id)
      setMessage(`Contraseña reseteada para ${resetDoctor.full_name}. Nueva: ${result.generated_password}`)
      setResetDoctor(null)
      load()
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo resetear la contraseña.")
    } finally {
      setResetting(false)
    }
  }

  function openReset(doctor: DoctorOut) {
    setResetDoctor(doctor)
    setResetGeneratedPass(generatePassword())
  }

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">Usuarios del Sistema</h1>
          <p className="mt-1 text-sm text-gray-500">
            Gestiona doctores y administradores
          </p>
        </div>
        <Button onClick={() => { setShowCreate(true); setGeneratedPassword(generatePassword()) }}>
          <Plus size={18} className="mr-1" /> Nuevo Usuario
        </Button>
      </div>

      {message && (
        <div className="mb-4 rounded-lg bg-emerald-50 px-4 py-3 text-sm text-emerald-700 border border-emerald-200">
          {message}
        </div>
      )}
      {error && (
        <div className="mb-4 rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700 border border-red-200">
          {error}
        </div>
      )}

      {loading ? (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-14 animate-pulse rounded-lg bg-gray-100" />
          ))}
        </div>
      ) : doctors.length === 0 ? (
        <div className="rounded-xl border border-dashed border-gray-300 p-12 text-center">
          <Users size={48} className="mx-auto mb-3 text-gray-300" />
          <p className="text-gray-500">No hay usuarios registrados</p>
          <Button className="mt-4" onClick={() => { setShowCreate(true); setGeneratedPassword(generatePassword()) }}>
            Crear primer usuario
          </Button>
        </div>
      ) : (
        <div className="overflow-x-auto rounded-xl border border-gray-200">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200 bg-gray-50 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                <th className="px-4 py-3">Nombre</th>
                <th className="px-4 py-3">Email</th>
                <th className="px-4 py-3">Rol</th>
                <th className="px-4 py-3">Estado</th>
                <th className="px-4 py-3">Creado</th>
                <th className="px-4 py-3 text-right">Acciones</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {doctors.map((doctor) => (
                <tr key={doctor.id} className="hover:bg-gray-50 transition-colors">
                  <td className="px-4 py-3 font-medium text-gray-800">{doctor.full_name}</td>
                  <td className="px-4 py-3 text-gray-500">{doctor.email}</td>
                  <td className="px-4 py-3">
                    <Badge variant={doctor.role === "admin" ? "neutral" : "info"}>
                      {doctor.role === "admin" ? "Admin" : "Doctor"}
                    </Badge>
                  </td>
                  <td className="px-4 py-3">
                    <Badge variant={doctor.is_active ? "success" : "danger"}>
                      {doctor.is_active ? "Activo" : "Inactivo"}
                    </Badge>
                  </td>
                  <td className="px-4 py-3 text-xs text-gray-400">
                    {new Date(doctor.created_at || "").toLocaleDateString("es-ES")}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <div className="flex items-center justify-end gap-2">
                      <Button variant="ghost" size="sm"
                        onClick={() => {
                          // Optimistic toggle
                          setDoctors((prev) =>
                            prev.map((d) =>
                              d.id === doctor.id ? { ...d, is_active: !d.is_active } : d,
                            ),
                          )
                          // Fire-and-forget save
                          updateAdminDoctor(doctor.id, { is_active: !doctor.is_active })
                            .catch(() => { load(); setError("Error al cambiar estado") })
                        }}>
                        {doctor.is_active ? "Desactivar" : "Activar"}
                      </Button>
                      <Button variant="secondary" size="sm" onClick={() => openReset(doctor)}>
                        Reset pass
                      </Button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Create modal */}
      {showCreate && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4"
          onClick={() => setShowCreate(false)}>
          <div className="w-full max-w-md rounded-xl bg-white p-6 shadow-lg"
            onClick={(e) => e.stopPropagation()}>
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-lg font-bold text-gray-800">Crear Usuario</h2>
              <button onClick={() => setShowCreate(false)} className="text-gray-400 hover:text-gray-600">
                <X size={20} />
              </button>
            </div>
            <form onSubmit={onCreate}>
              <div className="mb-3">
                <label className="mb-1 block text-sm font-medium text-gray-700">Nombre completo</label>
                <input required value={createName} onChange={(e) => setCreateName(e.target.value)}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm
                    focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500" />
              </div>
              <div className="mb-3">
                <label className="mb-1 block text-sm font-medium text-gray-700">Correo electrónico</label>
                <input required type="email" value={createEmail} onChange={(e) => setCreateEmail(e.target.value)}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm
                    focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500" />
              </div>
              <div className="mb-3">
                <label className="mb-1 block text-sm font-medium text-gray-700">Rol</label>
                <select value={createRole} onChange={(e) => setCreateRole(e.target.value as Role)}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm
                    focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500">
                  <option value="doctor">Doctor</option>
                  <option value="admin">Admin</option>
                </select>
              </div>
              <div className="mb-4 rounded-lg bg-amber-50 p-3 border border-amber-200">
                <div className="mb-1 text-xs text-gray-500">Contraseña generada automáticamente</div>
                <div className="flex items-center gap-2">
                  <code className="flex-1 rounded bg-white px-2 py-1 text-sm font-mono font-bold text-gray-800 border">
                    {generatedPassword}
                  </code>
                  <button type="button" onClick={() => navigator.clipboard?.writeText(generatedPassword)}
                    className="rounded p-1 text-gray-400 hover:text-gray-600" title="Copiar">
                    <Copy size={16} />
                  </button>
                  <button type="button" onClick={() => setGeneratedPassword(generatePassword())}
                    className="rounded p-1 text-gray-400 hover:text-gray-600" title="Regenerar">
                    <ArrowsClockwise size={16} />
                  </button>
                </div>
              </div>
              <div className="flex justify-end gap-2">
                <Button variant="secondary" type="button" onClick={() => setShowCreate(false)}>
                  Cancelar
                </Button>
                <Button type="submit" disabled={creating}>
                  {creating ? "Creando..." : "Crear Usuario"}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Reset password modal */}
      {resetDoctor && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4"
          onClick={() => setResetDoctor(null)}>
          <div className="w-full max-w-md rounded-xl bg-white p-6 shadow-lg"
            onClick={(e) => e.stopPropagation()}>
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-lg font-bold text-gray-800">Resetear Contraseña</h2>
              <button onClick={() => setResetDoctor(null)} className="text-gray-400 hover:text-gray-600">
                <X size={20} />
              </button>
            </div>
            <p className="mb-4 text-sm text-gray-600">
              ¿Resetear contraseña de <strong>{resetDoctor.full_name}</strong>?
            </p>
            <div className="mb-4 rounded-lg bg-amber-50 p-3 border border-amber-200">
              <div className="mb-1 text-xs text-gray-500">Nueva contraseña generada</div>
              <div className="flex items-center gap-2">
                <code className="flex-1 rounded bg-white px-2 py-1 text-sm font-mono font-bold text-gray-800 border">
                  {resetGeneratedPass}
                </code>
                <button type="button" onClick={() => navigator.clipboard?.writeText(resetGeneratedPass)}
                  className="rounded p-1 text-gray-400 hover:text-gray-600" title="Copiar">
                  <Copy size={16} />
                </button>
                <button type="button" onClick={() => setResetGeneratedPass(generatePassword())}
                  className="rounded p-1 text-gray-400 hover:text-gray-600" title="Regenerar">
                  <ArrowsClockwise size={16} />
                </button>
              </div>
            </div>
            <div className="mb-4 rounded-lg bg-red-50 p-3 text-xs text-red-700 border border-red-200">
              Al resetear, el usuario será forzado a cambiar su contraseña en el próximo inicio de sesión.
            </div>
            <form onSubmit={onResetPassword}>
              <div className="flex justify-end gap-2">
                <Button variant="secondary" type="button" onClick={() => setResetDoctor(null)}>
                  Cancelar
                </Button>
                <Button variant="danger" type="submit" disabled={resetting}>
                  {resetting ? "Reseteando..." : "Resetear Contraseña"}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
```

Note: The Badge component's variant prop uses `"success" | "warning" | "danger" | "neutral" | "info"`. We need to check what Badge supports. Let's use the existing variants. If "info" doesn't exist, use "neutral" for doctor role.

- [ ] **Step 2: Check Badge component variants**

Run:
```bash
cd frontend && grep -n "variant" src/components/ui/Badge.tsx
```

Expected: Shows the available variants. Adjust AdminUsers if needed.

- [ ] **Step 3: Verify TypeScript compiles**

Run:
```bash
cd frontend && npx tsc --noEmit 2>&1 | head -30
```

Expected: No new errors.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/pages/AdminUsers.tsx
git commit -m "feat: redesign AdminUsers with auto-generated passwords and modals"
```

---

### Task 13: Frontend — RequireAuth + Routes + AdminLayout

**Files:**
- Modify: `frontend/src/components/RequireAuth.tsx`
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/layouts/AdminLayout.tsx`

- [ ] **Step 1: Update RequireAuth with admin route protection**

Replace `frontend/src/components/RequireAuth.tsx`:

```tsx
import { Navigate, useLocation } from "react-router-dom"
import { useAuth } from "../context/AuthContext"

export default function RequireAuth({ children }: { children: React.ReactNode }) {
  const { token, session } = useAuth()
  const location = useLocation()

  if (!token) {
    return <Navigate to="/login" replace state={{ from: location }} />
  }
  if (session?.mustChangePassword) {
    return <Navigate to="/change-password" replace />
  }

  // Block non-admin users from admin routes
  const isAdminRoute = location.pathname.startsWith("/admin")
  if (isAdminRoute && session?.role !== "admin") {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-50 px-4">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-800">403</h1>
          <p className="mt-2 text-gray-500">No tienes permisos para acceder a esta sección.</p>
        </div>
      </div>
    )
  }

  return <>{children}</>
}
```

- [ ] **Step 2: Update App.tsx with new routes**

Replace `frontend/src/App.tsx`:

```tsx
import { Routes, Route, Navigate } from "react-router-dom"
import RequireAuth from "./components/RequireAuth"
import AdminLayout from "./layouts/AdminLayout"
import Login from "./pages/Login"
import AdminLogin from "./pages/AdminLogin"
import ChangePassword from "./pages/ChangePassword"
import ResetPassword from "./pages/ResetPassword"
import AdminUsers from "./pages/AdminUsers"
import Dashboard from "./pages/Dashboard"
import Patients from "./pages/Patients"
import PatientDetail from "./pages/PatientDetail"
import IntakeLinks from "./pages/IntakeLinks"
import Diets from "./pages/Diets"
import DietDetail from "./pages/DietDetail"
import DietWizard from "./pages/DietWizard"
import PublicIntake from "./pages/PublicIntake"
import NotFound from "./pages/NotFound"
import Trash from "./pages/Trash"

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/admin" element={<AdminLogin />} />
      <Route path="/change-password" element={<ChangePassword />} />
      <Route path="/reset-password" element={<ResetPassword />} />
      <Route path="/intake/:token" element={<PublicIntake />} />
      <Route
        path="/"
        element={
          <RequireAuth>
            <AdminLayout />
          </RequireAuth>
        }
      >
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<Dashboard />} />
        <Route path="patients" element={<Patients />} />
        <Route path="patients/:patientId" element={<PatientDetail />} />
        <Route path="intake-links" element={<Navigate to="/formularios" replace />} />
        <Route path="formularios" element={<IntakeLinks />} />
        <Route path="diets/new" element={<DietWizard />} />
        <Route path="diets/:dietId/regenerate" element={<DietWizard />} />
        <Route path="diets" element={<Diets />} />
        <Route path="diets/:dietId" element={<DietDetail />} />
        <Route path="trash" element={<Trash />} />
        <Route path="admin/users" element={<AdminUsers />} />
      </Route>
      <Route path="*" element={<NotFound />} />
    </Routes>
  )
}
```

- [ ] **Step 3: AdminLayout — no changes needed beyond what exists**

The existing AdminLayout.tsx already has `ADMIN_ITEM` in navigation and conditional rendering for admin role. This task confirms it works as-is. The admin sidebar is already handled by the existing layout.

- [ ] **Step 4: Verify TypeScript compiles**

Run:
```bash
cd frontend && npx tsc --noEmit 2>&1 | head -30
```

Expected: No new errors.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/RequireAuth.tsx frontend/src/App.tsx
git commit -m "feat: add admin routes, protect admin paths, add ResetPassword route"
```

---

### Task 14: End-to-End verification

**Files:** N/A

- [ ] **Step 1: Start backend and test endpoints**

Run:
```bash
cd backend && python -m pytest tests/ -x -q 2>&1 | tail -20
```

Expected: All tests pass (or note any pre-existing failures).

- [ ] **Step 2: Verify backend starts successfully**

Run:
```bash
cd backend && python -c "
from app.main import app
print('App loaded with routes:')
for r in app.routes:
    if hasattr(r, 'methods') and hasattr(r, 'path'):
        print(f'  {r.methods} {r.path}')
"
```

Expected: All routes including new ones (forgot-password, verify-reset-token, reset-password) show in output.

- [ ] **Step 3: Verify frontend builds**

Run:
```bash
cd frontend && npx vite build 2>&1 | tail -10
```

Expected: Build succeeds without errors.

- [ ] **Step 4: Final review pass — verify all spec requirements are covered**

Checklist:
- [ ] Admin can log in at `/admin` (AdminLogin.tsx + portal=admin validation)
- [ ] Doctor can log in at `/login` (Login.tsx + portal=doctor validation)
- [ ] Admin cannot log in at `/login` (403)
- [ ] Doctor cannot log in at `/admin` (403)
- [ ] Creating user generates password automatically
- [ ] Reset password generates password automatically
- [ ] must_change_password=true forces redirect to /change-password
- [ ] Forgot password sends email with reset link
- [ ] Reset link expires in 30 minutes
- [ ] Token is one-time use
- [ ] Reset password form validates strength and confirmation
- [ ] Success redirects to login after 3 seconds
- [ ] Email templates match existing branding (Dra. Acosta, emerald colors, logo)
- [ ] Responses are generic (no info leak)

- [ ] **Step 5: Commit any remaining changes**

```bash
git add -A
git commit -m "chore: final adjustments for admin user management system"
```
