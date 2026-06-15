# Formularios Registro + Actualización — Plan

> **For agentic workers:** Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans.

**Goal:** Add registration intake links (creates patient automatically) and update intake links (patient edits personal info + weight/height).

**Architecture:** Backend: `link_type` column on PatientIntakeLink, `patient_id` nullable for register links. Frontend: ShareModal with link type selector, PublicIntake renders full or simplified form based on `link_type`.

**Tech Stack:** FastAPI + SQLAlchemy, Alembic, React 19, Tailwind v4

**Spec:** `docs/superpowers/specs/2026-06-15-formularios-registro-actualizacion.md`

---

### Task 1: Migration + Model — add `link_type` and make `patient_id` nullable

**Files:**
- Modify: `backend/app/models.py:130-146`
- Create: `backend/alembic/versions/XXXX_add_link_type_make_patient_id_nullable.py`

- [ ] **Step 1: Update PatientIntakeLink model**

In `backend/app/models.py`, change `patient_id` to nullable and add `link_type`:
```python
class PatientIntakeLink(Base):
    __tablename__ = "patient_intake_links"

    id = Column(Integer, primary_key=True, index=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=True)  # NULLABLE for register links
    link_type = Column(String(20), nullable=False, default="register")  # "register" | "update"
    token = Column(String(80), unique=True, nullable=False, index=True)
    # ... rest stays the same
```

- [ ] **Step 2: Generate migration**

```bash
cd backend && source .venv/bin/activate && alembic revision --autogenerate -m "add link_type, make patient_id nullable"
```

- [ ] **Step 3: Run migration**

```bash
cd backend && source .venv/bin/activate && alembic upgrade head
```

- [ ] **Step 4: Verify backend still loads**

```bash
cd backend && source .venv/bin/activate && python -c "from app.main import app; print('OK')"
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/models.py backend/alembic/versions/
git commit -m "feat: add link_type column, make patient_id nullable for register links"
```

---

### Task 2: Update Pydantic schemas

**Files:**
- Modify: `backend/app/schemas.py:229-255`

- [ ] **Step 1: Update IntakeLinkCreate — patient_id optional for register**

```python
class IntakeLinkCreate(BaseModel):
    patient_id: Optional[int] = None
    link_type: Literal["register", "update"] = "register"
    expires_in_days: int = Field(default=7, ge=1, le=365)
    max_uses: int = Field(default=1, ge=1, le=50)
```

Add `Literal` import: `from typing import Literal, Optional`.

- [ ] **Step 2: Update IntakeLinkOut — add link_type, patient_id optional**

```python
class IntakeLinkOut(BaseModel):
    id: int
    doctor_id: int
    patient_id: Optional[int] = None
    link_type: str
    token: str
    # ... rest stays the same
```

- [ ] **Step 3: Update IntakeLinkPublicMeta — add link_type**

```python
class IntakeLinkPublicMeta(BaseModel):
    valid: bool
    link_type: Optional[str] = None  # so frontend knows which form to show
    expires_at: Optional[datetime] = None
    patient_first_name: Optional[str] = None
    patient_last_name: Optional[str] = None
    message: Optional[str] = None
```

- [ ] **Step 4: Commit**

```bash
git add backend/app/schemas.py
git commit -m "feat: update schemas for register/update link types"
```

---

### Task 3: Update intake_links.py — create_link and submit adapted

**Files:**
- Modify: `backend/app/api/intake_links.py`

- [ ] **Step 1: Adapt `create_link` for register links (no patient_id required)**

```python
@router.post("", response_model=IntakeLinkOut, status_code=status.HTTP_201_CREATED)
async def create_link(
    body: IntakeLinkCreate,
    db: AsyncSession = Depends(get_db),
    doctor: Doctor = Depends(get_current_doctor),
):
    if body.link_type == "update":
        if body.patient_id is None:
            raise HTTPException(status_code=400, detail="patient_id required for update links")
        patient = await db.get(Patient, body.patient_id)
        if patient is None or patient.doctor_id != doctor.id:
            raise HTTPException(status_code=404, detail="Patient not found")

    token = secrets.token_urlsafe(32)
    expires_at = utcnow() + timedelta(days=body.expires_in_days)
    link = PatientIntakeLink(
        doctor_id=doctor.id,
        patient_id=body.patient_id,  # None for register
        link_type=body.link_type,
        token=token,
        expires_at=expires_at,
        max_uses=body.max_uses,
    )
    db.add(link)
    await db.commit()
    await db.refresh(link)
    return link
```

- [ ] **Step 2: Update `public_validate` to return link_type**

```python
@router.get("/public/{token}", response_model=IntakeLinkPublicMeta)
async def public_validate(token: str, db: AsyncSession = Depends(get_db)):
    # ... existing validation logic ...
    patient = await db.get(Patient, link.patient_id) if link.patient_id else None
    return IntakeLinkPublicMeta(
        valid=True,
        link_type=link.link_type,
        expires_at=link.expires_at,
        patient_first_name=patient.first_name if patient else None,
        patient_last_name=patient.last_name if patient else None,
    )
```

- [ ] **Step 3: Adapt `public_submit` to create patient when none exists (register flow)**

Replace the `if patient is None` block (lines 140-145):
```python
if link.link_type == "register" and link.patient_id is None:
    # Create new patient
    patient = Patient(
        doctor_id=link.doctor_id,
        first_name=body.first_name,
        last_name=body.last_name,
        birth_date=body.birth_date,
        sex=body.sex,
        whatsapp=body.whatsapp,
        email=str(body.email) if body.email else None,
        country=body.country,
        city=body.city,
        source="intake_link",
    )
    db.add(patient)
    await db.flush()
    link.patient_id = patient.id
else:
    patient = await db.get(Patient, link.patient_id)
    if patient is None:
        raise HTTPException(status_code=404, detail="Patient not found")
```

- [ ] **Step 4: Limit `public_update` to only allowed fields**

Change the `patient_fields` list in `public_update` (line 255-258):
```python
patient_fields = [
    "first_name", "last_name", "whatsapp", "email",
    "country", "city",
]
```

Remove ALL profile fields from the update (lines 265-286) — the update link should NOT modify clinical profile. Remove metric fields except weight_kg and height_cm.

```python
# Only weight and height in metrics
metric_fields = ["weight_kg", "height_cm"]
```

- [ ] **Step 5: Verify backend loads**

```bash
cd backend && source .venv/bin/activate && python -c "from app.main import app; print('OK')"
```

- [ ] **Step 6: Commit**

```bash
git add backend/app/api/intake_links.py
git commit -m "feat: adapt intake links for register/update types, limit update fields"
```

---

### Task 4: Frontend types + API

**Files:**
- Modify: `frontend/src/types/index.ts`
- Modify: `frontend/src/services/api.ts`

- [ ] **Step 1: Add link_type to IntakeLink type**

In types/index.ts, add `link_type`:
```typescript
export type IntakeLink = {
  id: number
  doctor_id: number
  patient_id: number | null
  link_type: string
  token: string
  status: string
  expires_at: string
  max_uses: number
  use_count: number
  last_used_at?: string | null
  created_at: string
}

export type IntakePublicMeta = {
  valid: boolean
  link_type?: string | null
  expires_at?: string | null
  patient_first_name?: string | null
  patient_last_name?: string | null
  message?: string | null
}
```

- [ ] **Step 2: Add updateIntakeForm to api.ts + update createIntakeLink**

Update `createIntakeLink` body:
```typescript
export function createIntakeLink(body: {
  patient_id?: number
  link_type?: string
  expires_in_days: number
  max_uses?: number
}) {
  return authFetch("/intake-links", {
    method: "POST",
    body: JSON.stringify(body),
  }).then((r) => parseJson<IntakeLink>(r))
}
```

Add `updateIntakeForm`:
```typescript
export function updateIntakeForm(token: string, body: Record<string, unknown>) {
  return fetch(`${API_BASE_URL}/intake-links/public/${token}/update`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  }).then((r) => {
    if (!r.ok) throw new Error("Error al actualizar datos")
    return r.json()
  })
}
```

- [ ] **Step 3: Verify TS**

```bash
cd frontend && npx tsc --noEmit
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/types/index.ts frontend/src/services/api.ts
git commit -m "feat: add link_type to types, updateIntakeForm to api"
```

---

### Task 5: ShareModal — link type selector + remove WhatsApp

**Files:**
- Modify: `frontend/src/components/sharing/ShareModal.tsx`

- [ ] **Step 1: Add link_type state and patientId becomes optional**

```tsx
import { useState } from "react"
import { AnimatePresence, motion } from "framer-motion"
import { X, Spinner, Check, Copy, Envelope, Share } from "@phosphor-icons/react"  // removed WhatsappLogo
import { createIntakeLink } from "../../services/api"
import { useToast } from "../../context/ToastContext"
import type { IntakeLink } from "../../types"

type ShareModalProps = {
  open: boolean
  onClose: () => void
  patientId?: number       // optional for register links
  patientName?: string     // optional
}
```

- [ ] **Step 2: Add link_type selector to Step 1**

After the expiration dropdown, add a type selector:
```tsx
<div>
  <label className="block text-sm font-medium text-gray-700 mb-1.5">
    Tipo de formulario
  </label>
  <select
    value={linkType}
    onChange={(e) => setLinkType(e.target.value)}
    className="w-full rounded-xl border border-gray-300 px-3 py-2.5 text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
  >
    <option value="register">📝 Registro — nuevo paciente</option>
    <option value="update">🔄 Actualización — paciente existente</option>
  </select>
</div>
```

Add state: `const [linkType, setLinkType] = useState<"register" | "update">("register")`

- [ ] **Step 3: Remove WhatsApp fallback in Step 2**

Replace the WhatsApp+Email fallback block (lines 223-242) with just Email:
```tsx
{!hasWebShare && (
  <a
    href={emailLink}
    className="flex items-center justify-center gap-2 rounded-xl bg-gray-600 px-4 py-3 text-sm font-semibold text-white hover:bg-gray-700 transition-colors shadow-sm"
  >
    <Envelope size={18} />
    Enviar por correo
  </a>
)}
```

Update handleCreate to send `link_type`:
```tsx
const result = await createIntakeLink({
  patient_id: linkType === "update" ? patientId : undefined,
  link_type: linkType,
  expires_in_days: selectedDays,
})
```

- [ ] **Step 4: Update IntakeLinks.tsx usage**

When opening ShareModal for register, pass patientId as optional.

- [ ] **Step 5: Verify TS**

```bash
cd frontend && npx tsc --noEmit
```

- [ ] **Step 6: Commit**

```bash
git add frontend/src/components/sharing/ShareModal.tsx
git commit -m "feat: add link type selector to ShareModal, remove WhatsApp direct button"
```

---

### Task 6: PublicIntake — detect link_type, show full or simplified form

**Files:**
- Modify: `frontend/src/pages/PublicIntake.tsx`

- [ ] **Step 1: Detect link_type on validate**

In the `useEffect` that validates the token (line 29-42), save `link_type`:
```tsx
const [linkType, setLinkType] = useState<"register" | "update">("register")

// In the validate callback:
validateIntakeToken(token)
  .then((m) => {
    if (!cancelled) {
      setMeta(m)
      if (m.link_type) setLinkType(m.link_type as "register" | "update")
    }
  })
```

- [ ] **Step 2: Conditional rendering**

- If `linkType === "register"` → show ALL fields (same as current form)
- If `linkType === "update"` → show only: nombre, apellido, email, whatsapp, país, ciudad, peso (WeightInput), altura (HeightInput). Pre-llenar datos si el paciente ya existe.

For the submit:
- If register → POST `/intake-links/public/{token}/submit` (existing)
- If update → PUT `/intake-links/public/{token}/update` (new, only sends changed fields)

```tsx
async function onSubmit(e: FormEvent) {
  e.preventDefault()
  if (!token) return
  // ... build body ...
  try {
    if (linkType === "update") {
      await updateIntakeForm(token, updateBody)
    } else {
      await submitIntakeForm(token, body)
    }
    setDone(true)
  } catch (err) {
    setError(err instanceof Error ? err.message : "Error")
  }
}
```

- [ ] **Step 3: Verify TS**

```bash
cd frontend && npx tsc --noEmit
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/pages/PublicIntake.tsx
git commit -m "feat: PublicIntake detects link_type — full form for register, simplified for update"
```

---

### Task 7: IntakeLinks page — show link type in list

**Files:**
- Modify: `frontend/src/pages/IntakeLinks.tsx`

- [ ] **Step 1: Show link_type badge column**

In the intake links table, add a Badge column showing:
- "📝 Registro" → Badge emerald
- "🔄 Actualización" → Badge blue

- [ ] **Step 2: Commit**

```bash
git add frontend/src/pages/IntakeLinks.tsx
git commit -m "feat: show link type badge in intake links list"
```

---

### Task 8: Build verification

- [ ] **Step 1: TypeScript check**

```bash
cd frontend && npx tsc --noEmit
```

- [ ] **Step 2: Frontend build**

```bash
cd frontend && npm run build
```

- [ ] **Step 3: Backend check**

```bash
cd backend && source .venv/bin/activate && python -c "from app.main import app; print('Backend OK')"
```

- [ ] **Step 4: Final commit**

```bash
git add -A && git commit -m "chore: final adjustments after register/update intake forms"
```

---

## Verification Summary

| # | Check | How |
|---|-------|-----|
| 1 | Create register link without patient | ShareModal → "Registro" → patientId not needed |
| 2 | Submit registration → patient created | Open link → fill form → submit → new patient in list |
| 3 | Create update link for existing patient | ShareModal → "Actualización" → select patient |
| 4 | Submit update → only personal+metrics changed | Open link → modify weight → verify profile unchanged |
| 5 | No WhatsApp direct button anywhere | Check ShareModal |
| 6 | ShareModal shows 3 methods: Compartir, Copiar, Correo | Check ShareModal step 2 |
| 7 | Expiration configurable | Check dropdown: 1, 3, 7, 14, 30 days |
| 8 | IntakeLinks shows type badge | Open /formularios |
| 9 | Build | `npm run build` passes |
