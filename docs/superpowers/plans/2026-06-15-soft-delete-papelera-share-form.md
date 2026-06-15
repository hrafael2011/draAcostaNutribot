# Soft Delete / Papelera + Compartir Formulario — Plan

> **For agentic workers:** Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans.

**Goal:** Implement soft delete with a recycle bin for patients and diets, and add Web Share API to form link sharing.

**Architecture:** Backend: `deleted_at` column on patients+diets tables, new `/trash` + `/restore` + `/hard-delete` endpoints, existing endpoints filter out soft-deleted records. Frontend: new `/trash` page with Pacientes/Dietas tabs, delete/restore actions on list pages, ShareModal gets Web Share API.

**Tech Stack:** FastAPI + SQLAlchemy (asyncpg), Alembic, React 19, Tailwind CSS v4

**Spec:** `docs/superpowers/specs/2026-06-15-soft-delete-papelera-share-form.md`

---

### Task 1: Alembic migration — add `deleted_at` to patients and diets

**Files:**
- Modify: `backend/app/models.py:57-58,148-165`
- Create: `backend/alembic/versions/XXXX_add_deleted_at_for_soft_delete.py`

- [ ] **Step 1: Add `deleted_at` column to Patient and Diet models**

In `backend/app/models.py`, add `deleted_at` column to Patient (after `is_archived` line 58):
```python
deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, default=None)
```

Add same column to Diet model (after `doctor_id` line ~153):
```python
deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, default=None)
```

Import `datetime` from `datetime` if not already imported.

- [ ] **Step 2: Generate migration**

```bash
cd backend && source .venv/bin/activate && alembic revision --autogenerate -m "add deleted_at for soft delete"
```

- [ ] **Step 3: Verify migration SQL is correct**

Check the generated migration file under `backend/alembic/versions/` — should contain:
```sql
ALTER TABLE patients ADD COLUMN deleted_at TIMESTAMPTZ;
ALTER TABLE diets ADD COLUMN deleted_at TIMESTAMPTZ;
```

- [ ] **Step 4: Run migration**

```bash
cd backend && source .venv/bin/activate && alembic upgrade head
```

Expected: `alembic upgrade head` succeeds.

- [ ] **Step 5: Commit**

```bash
git add backend/app/models.py backend/alembic/versions/
git commit -m "feat: add deleted_at column to patients and diets for soft delete"
```

---

### Task 2: Backend trash API endpoints

**Files:**
- Create: `backend/app/api/trash.py`
- Modify: `backend/app/api/router.py:11`

- [ ] **Step 1: Create trash router with endpoints**

Create `backend/app/api/trash.py`:

```python
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.security import get_current_doctor
from app.models import Patient, Diet, Doctor

router = APIRouter(prefix="/trash", tags=["trash"])

@router.get("/patients")
async def list_trashed_patients(
    search: str = "",
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    doctor: Doctor = Depends(get_current_doctor),
    db: AsyncSession = Depends(get_db),
):
    """List soft-deleted patients."""
    query = select(Patient).where(
        Patient.doctor_id == doctor.id,
        Patient.deleted_at.isnot(None),
    )
    if search:
        query = query.where(
            Patient.first_name.ilike(f"%{search}%") |
            Patient.last_name.ilike(f"%{search}%")
        )
    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar() or 0
    rows = (await db.execute(
        query.order_by(Patient.deleted_at.desc())
        .offset((page - 1) * page_size).limit(page_size)
    )).scalars().all()
    return {
        "items": [{
            "id": p.id,
            "first_name": p.first_name,
            "last_name": p.last_name,
            "email": p.email,
            "deleted_at": p.deleted_at.isoformat() if p.deleted_at else None,
        } for p in rows],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/diets")
async def list_trashed_diets(
    search: str = "",
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    doctor: Doctor = Depends(get_current_doctor),
    db: AsyncSession = Depends(get_db),
):
    """List soft-deleted diets with patient name."""
    query = (
        select(Diet, Patient.first_name, Patient.last_name)
        .join(Patient, Diet.patient_id == Patient.id)
        .where(
            Patient.doctor_id == doctor.id,
            Diet.deleted_at.isnot(None),
        )
    )
    if search:
        query = query.where(
            Patient.first_name.ilike(f"%{search}%") |
            Patient.last_name.ilike(f"%{search}%")
        )
    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar() or 0
    rows = (await db.execute(
        query.order_by(Diet.deleted_at.desc())
        .offset((page - 1) * page_size).limit(page_size)
    )).all()
    return {
        "items": [{
            "diet_id": d.id,
            "patient_id": d.patient_id,
            "patient_name": f"{fn} {ln}",
            "title": d.title,
            "deleted_at": d.deleted_at.isoformat() if d.deleted_at else None,
        } for d, fn, ln in rows],
        "total": total,
        "page": page,
        "page_size": page_size,
    }
```

- [ ] **Step 2: Mount trash router in router.py**

Add import and include line in `backend/app/api/router.py`:
```python
from app.api import admin, auth, doctors, patients, intake_links, diets, dashboard, health, trash
api_router.include_router(trash.router, tags=["trash"])
```

- [ ] **Step 3: Verify TypeScript — wait, this is Python. Verify Python syntax.**

```bash
cd backend && source .venv/bin/activate && python -c "from app.api.trash import *; print('OK')"
```

- [ ] **Step 4: Commit**

```bash
git add backend/app/api/trash.py backend/app/api/router.py
git commit -m "feat: add trash API endpoints for listing soft-deleted patients and diets"
```

---

### Task 3: Update patients.py — soft delete + restore + hard delete endpoints + filter

**Files:**
- Modify: `backend/app/api/patients.py`

- [ ] **Step 1: Add soft-delete, restore and hard-delete endpoints**

Add after the existing `GET /patients/{patient_id}/summary` endpoint or at the end of the file:

```python
@router.post("/{patient_id}/soft-delete")
async def soft_delete_patient(
    patient_id: int,
    doctor: Doctor = Depends(get_current_doctor),
    db: AsyncSession = Depends(get_db),
):
    patient = await _get_patient_or_404(patient_id, doctor.id, db)
    patient.deleted_at = datetime.now(timezone.utc)
    # Also soft-delete all diets for this patient
    diets_q = select(Diet).where(Diet.patient_id == patient_id, Diet.deleted_at.is_(None))
    diets = (await db.execute(diets_q)).scalars().all()
    for d in diets:
        d.deleted_at = patient.deleted_at
    await db.commit()
    return {"ok": True}


@router.post("/{patient_id}/restore")
async def restore_patient(
    patient_id: int,
    doctor: Doctor = Depends(get_current_doctor),
    db: AsyncSession = Depends(get_db),
):
    patient = await _get_patient_or_404(patient_id, doctor.id, db)
    patient.deleted_at = None
    # Restore all diets that were soft-deleted at the same time
    diets_q = select(Diet).where(Diet.patient_id == patient_id, Diet.deleted_at.isnot(None))
    diets = (await db.execute(diets_q)).scalars().all()
    for d in diets:
        d.deleted_at = None
    await db.commit()
    return {"ok": True}


@router.delete("/{patient_id}/hard-delete")
async def hard_delete_patient(
    patient_id: int,
    doctor: Doctor = Depends(get_current_doctor),
    db: AsyncSession = Depends(get_db),
):
    patient = await _get_patient_or_404(patient_id, doctor.id, db)
    # Delete related records
    await db.execute(delete(PatientProfile).where(PatientProfile.patient_id == patient_id))
    await db.execute(delete(PatientMetrics).where(PatientMetrics.patient_id == patient_id))
    await db.execute(delete(Diet).where(Diet.patient_id == patient_id))
    await db.execute(delete(PatientIntakeLink).where(PatientIntakeLink.patient_id == patient_id))
    await db.delete(patient)
    await db.commit()
    return {"ok": True}
```

Add imports at top: `from datetime import datetime, timezone; from sqlalchemy import delete`

- [ ] **Step 2: Add `deleted_at IS NULL` filter to GET /patients**

In `list_patients()`, add to conditions:
```python
conditions.append(Patient.deleted_at.is_(None))
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/api/patients.py
git commit -m "feat: add soft-delete, restore, hard-delete for patients + filter deleted from list"
```

---

### Task 4: Update diets.py — soft delete + restore + hard delete endpoints + filter

**Files:**
- Modify: `backend/app/api/diets.py`

- [ ] **Step 1: Add soft-delete, restore, hard-delete endpoints**

```python
@router.post("/{diet_id}/soft-delete")
async def soft_delete_diet(
    diet_id: int,
    doctor: Doctor = Depends(get_current_doctor),
    db: AsyncSession = Depends(get_db),
):
    diet = await _get_diet_or_404(diet_id, doctor.id, db)
    diet.deleted_at = datetime.now(timezone.utc)
    await db.commit()
    return {"ok": True}


@router.post("/{diet_id}/restore")
async def restore_diet(
    diet_id: int,
    doctor: Doctor = Depends(get_current_doctor),
    db: AsyncSession = Depends(get_db),
):
    diet = await _get_diet_or_404(diet_id, doctor.id, db)
    diet.deleted_at = None
    await db.commit()
    return {"ok": True}


@router.delete("/{diet_id}/hard-delete")
async def hard_delete_diet(
    diet_id: int,
    doctor: Doctor = Depends(get_current_doctor),
    db: AsyncSession = Depends(get_db),
):
    diet = await _get_diet_or_404(diet_id, doctor.id, db)
    await db.execute(delete(DietVersion).where(DietVersion.diet_id == diet_id))
    await db.delete(diet)
    await db.commit()
    return {"ok": True}
```

- [ ] **Step 2: Add `deleted_at IS NULL` filter to GET /diets**

In `list_diets()`, add:
```python
conditions.append(Diet.deleted_at.is_(None))
```

- [ ] **Step 3: Update diet_eligibility.py + diet_service.py**

In `diet_eligibility.py`, add check in `diet_generation_blockers`:
```python
if patient.deleted_at:
    return ["El paciente ha sido eliminado"]
```

In `diet_service.py` `create_new_diet`, add early check after patient fetch:
```python
if patient.deleted_at:
    raise HTTPException(status_code=400, detail="Cannot create diet for a deleted patient")
```

- [ ] **Step 4: Commit**

```bash
git add backend/app/api/diets.py backend/app/logic/diet_eligibility.py backend/app/services/diet_service.py
git commit -m "feat: add soft-delete/restore/hard-delete for diets + filter deleted from list"
```

---

### Task 5: Frontend API functions

**Files:**
- Modify: `frontend/src/services/api.ts`

- [ ] **Step 1: Add soft/hard delete + trash + restore functions**

```typescript
// ── Trash / Soft Delete ────────────────────────────────────────────

export function getTrashPatients(search?: string, page?: number, pageSize?: number) {
  const params = new URLSearchParams()
  if (search) params.set("search", search)
  if (page) params.set("page", String(page))
  if (pageSize) params.set("page_size", String(pageSize))
  const qs = params.toString()
  return authFetch(`/trash/patients${qs ? "?" + qs : ""}`).then((r) => parseJson<PaginatedTrashPatients>(r))
}

export function getTrashDiets(search?: string, page?: number, pageSize?: number) {
  const params = new URLSearchParams()
  if (search) params.set("search", search)
  if (page) params.set("page", String(page))
  if (pageSize) params.set("page_size", String(pageSize))
  const qs = params.toString()
  return authFetch(`/trash/diets${qs ? "?" + qs : ""}`).then((r) => parseJson<PaginatedTrashDiets>(r))
}

export function softDeletePatient(patientId: number) {
  return authFetch(`/patients/${patientId}/soft-delete`, { method: "POST" }).then(r => r.json())
}

export function restorePatient(patientId: number) {
  return authFetch(`/patients/${patientId}/restore`, { method: "POST" }).then(r => r.json())
}

export function hardDeletePatient(patientId: number) {
  return authFetch(`/patients/${patientId}/hard-delete`, { method: "DELETE" }).then(r => r.json())
}

export function softDeleteDiet(dietId: number) {
  return authFetch(`/diets/${dietId}/soft-delete`, { method: "POST" }).then(r => r.json())
}

export function restoreDiet(dietId: number) {
  return authFetch(`/diets/${dietId}/restore`, { method: "POST" }).then(r => r.json())
}

export function hardDeleteDiet(dietId: number) {
  return authFetch(`/diets/${dietId}/hard-delete`, { method: "DELETE" }).then(r => r.json())
}
```

Add types for the response:
```typescript
export type TrashPatientItem = {
  id: number
  first_name: string
  last_name: string
  email: string | null
  deleted_at: string
}

export type TrashDietItem = {
  diet_id: number
  patient_id: number
  patient_name: string
  title: string | null
  deleted_at: string
}

export type PaginatedTrashPatients = {
  items: TrashPatientItem[]
  total: number
  page: number
  page_size: number
}

export type PaginatedTrashDiets = {
  items: TrashDietItem[]
  total: number
  page: number
  page_size: number
}
```

- [ ] **Step 2: Verify TypeScript compilation**

```bash
cd frontend && npx tsc --noEmit
```

Expected: no new TS errors.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/services/api.ts
git commit -m "feat: add API functions for soft-delete, restore, hard-delete and trash listing"
```

---

### Task 6: Create Trash page

**Files:**
- Create: `frontend/src/pages/Trash.tsx`

- [ ] **Step 1: Create Trash.tsx page**

Full page with tabs, search, patient/diet listings, restore and hard-delete actions.

- Two tabs: "🧑 Pacientes" and "📋 Dietas"
- Search input filtering by patient name
- Table per tab with: name, deleted date, actions (Restaurar / Eliminar permanentemente)
- "Eliminar permanentemente" shows a confirm dialog
- Empty state when no items
- Auto-refresh after restore/delete

- [ ] **Step 2: Add route in App.tsx**

```tsx
import Trash from "./pages/Trash"
// ... in the routes:
<Route path="trash" element={<Trash />} />
```

- [ ] **Step 3: Verify TypeScript compilation**

```bash
cd frontend && npx tsc --noEmit
```

Expected: no new TS errors.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/pages/Trash.tsx frontend/src/App.tsx
git commit -m "feat: add Trash page with Pacientes/Dietas tabs, restore and hard-delete"
```

---

### Task 7: Add sidebar link to Trash

**Files:**
- Modify: `frontend/src/layouts/AdminLayout.tsx:23-28`

- [ ] **Step 1: Add Trash icon import and NAV_ITEMS entry**

```tsx
import { Trash } from "@phosphor-icons/react" // add to existing imports
```

Add to NAV_ITEMS array:
```tsx
const NAV_ITEMS = [
  { to: "/dashboard", label: "Dashboard", icon: House },
  { to: "/patients", label: "Pacientes", icon: Users },
  { to: "/diets", label: "Dietas", icon: BowlFood },
  { to: "/formularios", label: "Formularios", icon: LinkSimple },
  { to: "/trash", label: "Papelera", icon: Trash },
]
```

Add breadcrumb label:
```tsx
BREADCRUMB_LABELS: Record<string, string> = {
  // ...existing
  trash: "Papelera",
}
```

- [ ] **Step 2: Verify TypeScript compilation**

```bash
cd frontend && npx tsc --noEmit
```

Expected: no new TS errors.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/layouts/AdminLayout.tsx
git commit -m "feat: add Papelera link to sidebar navigation"
```

---

### Task 8: Add delete option to PatientRow

**Files:**
- Modify: `frontend/src/components/patients/PatientRow.tsx`

- [ ] **Step 1: Add "🗑️ Eliminar" option to action menu**

Replace the "Enviar formulario" button with "Eliminar paciente":

```tsx
import { Trash, User, BowlFood, Pencil } from "@phosphor-icons/react" // removed Envelope, added Trash
```

Replace the share button (line 72-74):
```tsx
<button onClick={() => { setMenuOpen(false); onDelete?.(patient); }} className="flex items-center gap-2 px-3 py-2 text-sm text-slate-600 hover:bg-slate-50 w-full text-left">
  <Trash size={16} /> Eliminar paciente
</button>
```

Update Props type:
```tsx
type PatientRowProps = {
  patient: Patient;
  summary?: PatientSummary | null;
  onDelete?: (patient: Patient) => void;
};
```

Remove the `onShare` prop. Update the function signature.

- [ ] **Step 2: Verify TypeScript compilation**

```bash
cd frontend && npx tsc --noEmit
```

Expected: no new TS errors.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/patients/PatientRow.tsx
git commit -m "feat: replace share with delete option in PatientRow action menu"
```

---

### Task 9: Add delete option to Diets.tsx + update Patients.tsx

**Files:**
- Modify: `frontend/src/pages/Diets.tsx`
- Modify: `frontend/src/pages/Patients.tsx`

- [ ] **Step 1: Add delete button per diet row in Diets.tsx**

In the diet listing (around lines 649-678), add a delete button/icon to each row:
```tsx
<button
  onClick={() => handleDeleteDiet(d.id)}
  className="p-1.5 rounded-lg text-slate-400 hover:text-red-500 hover:bg-red-50 transition-all opacity-0 group-hover:opacity-100"
  title="Eliminar dieta"
>
  <Trash size={16} />
</button>
```

Add handler:
```tsx
const handleDeleteDiet = async (dietId: number) => {
  if (!window.confirm("¿Eliminar esta dieta? Se moverá a la papelera.")) return
  try {
    await softDeleteDiet(dietId)
    refresh()
    addToast("Dieta movida a la papelera", "success")
  } catch {
    addToast("Error al eliminar dieta", "error")
  }
}
```

- [ ] **Step 2: Add delete handler in Patients.tsx**

Add import and state:
```tsx
import { softDeletePatient } from "../services/api"
```

Add handler:
```tsx
const handleDeletePatient = async (patient: Patient) => {
  if (!window.confirm(`¿Eliminar a ${patient.first_name} ${patient.last_name}? Se moverá a la papelera.`)) return
  try {
    await softDeletePatient(patient.id)
    refresh()
    addToast("Paciente movido a la papelera", "success")
  } catch {
    addToast("Error al eliminar paciente", "error")
  }
}
```

Pass `onDelete={handleDeletePatient}` to PatientRow.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/pages/Diets.tsx frontend/src/pages/Patients.tsx
git commit -m "feat: add delete buttons on patient list and diet list"
```

---

### Task 10: Share form with Web Share API

**Files:**
- Modify: `frontend/src/components/sharing/ShareModal.tsx`

- [ ] **Step 1: Add Web Share button to ShareModal Step 2**

Replace the WhatsApp + Correo buttons section (lines 189-206) with conditional rendering:

```tsx
<div className="flex gap-3">
  {/* Copy button always visible */}
  <button
    onClick={() => handleCopy(url)}
    className="flex flex-1 items-center justify-center gap-2 rounded-xl bg-emerald-600 px-4 py-3 text-sm font-semibold text-white hover:bg-emerald-700 transition-colors shadow-sm"
  >
    {copied ? (
      <><Check size={18} /><span>¡Copiado!</span></>
    ) : (
      <><Copy size={18} /><span>Copiar enlace</span></>
    )}
  </button>

  {/* Share button (Web Share API on mobile) */}
  <button
    onClick={handleShare}
    className="flex flex-1 items-center justify-center gap-2 rounded-xl border-2 border-emerald-500 text-emerald-700 px-4 py-3 text-sm font-semibold hover:bg-emerald-50 transition-colors shadow-sm"
  >
    <Share size={18} />
    Compartir
  </button>
</div>

{!hasWebShare && (
  <div className="flex gap-3">
    <a href={waLink} target="_blank" rel="noopener noreferrer"
      className="flex flex-1 items-center justify-center gap-2 rounded-xl bg-green-500 px-4 py-3 text-sm font-semibold text-white hover:bg-green-600 transition-colors shadow-sm">
      <WhatsappLogo size={18} weight="fill" /> WhatsApp
    </a>
    <a href={emailLink}
      className="flex flex-1 items-center justify-center gap-2 rounded-xl bg-gray-600 px-4 py-3 text-sm font-semibold text-white hover:bg-gray-700 transition-colors shadow-sm">
      <Envelope size={18} /> Correo
    </a>
  </div>
)}
```

Add the `handleShare` function:
```tsx
import { Share } from "@phosphor-icons/react" // add to imports

const hasWebShare = typeof navigator !== "undefined" && !!navigator.share

const handleShare = async () => {
  if (!url) return
  try {
    await navigator.share({
      title: "Completa tu ficha nutricional - Dra. Acosta",
      text: "La Dra. Acosta te invita a completar tu ficha nutricional:",
      url: url,
    })
  } catch (err) {
    if (err instanceof DOMException && err.name === "AbortError") return
    addToast("Error al compartir", "error")
  }
}
```

- [ ] **Step 2: Verify TypeScript compilation**

```bash
cd frontend && npx tsc --noEmit
```

Expected: no new TS errors.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/sharing/ShareModal.tsx
git commit -m "feat: add Web Share API for form link sharing, keep WhatsApp/Email fallback on desktop"
```

---

### Task 11: Build verification

**Files:**
- (none) — verification only

- [ ] **Step 1: TypeScript check**

```bash
cd frontend && npx tsc --noEmit
```

Expected: no errors.

- [ ] **Step 2: Frontend build**

```bash
cd frontend && npm run build
```

Expected: build succeeds.

- [ ] **Step 3: Backend import check**

```bash
cd backend && source .venv/bin/activate && python -c "from app.main import app; print('Backend OK')"
```

Expected: prints "Backend OK".

- [ ] **Step 4: Final commit**

```bash
git add -A
git commit -m "chore: final adjustments after soft delete and share form implementation"
```

---

## Verification Summary

| # | What to check | How |
|---|---------------|-----|
| 1 | Backend starts without errors | `uvicorn app.main:app` |
| 2 | Frontend builds | `npm run build` |
| 3 | Patients list excludes soft-deleted records | Visit /patients after deleting one |
| 4 | Diets list excludes soft-deleted records | Visit /diets after deleting one |
| 5 | Trash page shows deleted patients | Visit /trash → "Pacientes" tab |
| 6 | Trash page shows deleted diets | Visit /trash → "Dietas" tab |
| 7 | Restore patient from trash → appears in patients list | Click "Restaurar" |
| 8 | Hard delete removes permanently | Click "Eliminar permanentemente" → confirm → record gone |
| 9 | Share form via Web Share API on mobile | ShareModal → "Compartir" → native menu opens |
| 10 | Share form shows WhatsApp/Email fallback on desktop | ShareModal → fallback buttons visible |
| 11 | Sidebar shows "Papelera" link | Visit any page → see sidebar |
