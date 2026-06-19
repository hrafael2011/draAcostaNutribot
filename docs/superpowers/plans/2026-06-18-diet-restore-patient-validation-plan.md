# Diet Restore — Patient Validation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prevent restoring a diet whose patient is still soft-deleted, and show the backend error message in the frontend.

**Architecture:** Add a patient `deleted_at` check in the `restore_diet` FastAPI endpoint (409 Conflict if patient is trashed). In the frontend `Trash.tsx`, capture the error object in the catch block and display `err.message` via toast instead of a generic string.

**Tech Stack:** FastAPI (Python), SQLAlchemy async, React + TypeScript

---

### Task 1: Backend — Validate patient is not deleted in `restore_diet`

**Files:**
- Modify: `backend/app/api/diets.py:441-452`

- [ ] **Step 1: Add patient check to restore_diet endpoint**

Replace the `restore_diet` function body. After the existing diet existence/ownership check, query the patient and raise 409 if the patient is soft-deleted:

```python
@router.post("/{diet_id}/restore")
async def restore_diet(
    diet_id: int,
    db: AsyncSession = Depends(get_db),
    doctor: Doctor = Depends(get_current_doctor),
):
    diet = await db.get(Diet, diet_id)
    if diet is None or diet.doctor_id != doctor.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dieta no encontrada")
    # Check if the associated patient is in the trash
    patient = await db.get(Patient, diet.patient_id)
    if patient and patient.deleted_at is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No se puede restaurar la dieta porque el paciente está en la papelera. Restaure al paciente primero."
        )
    diet.deleted_at = None
    await db.commit()
    return {"ok": True}
```

- [ ] **Step 2: Verify Patient model is already imported in diets.py**

Check the imports at the top of `backend/app/api/diets.py` for `Patient`. If not present, add it to the imports from `app.models`:

```python
from app.models import Diet, DietVersion, Patient
```

- [ ] **Step 3: Start backend and test manually**

Run: `cd backend && uvicorn app.main:app --reload --port 8000`

Test via curl (or frontend):
1. Soft-delete a patient (POST `/patients/{id}/soft-delete`) — this also soft-deletes the patient's diets
2. Try to restore one of those diets (POST `/diets/{id}/restore`)
3. Expected: HTTP 409 with message `"No se puede restaurar la dieta porque el paciente está en la papelera. Restaure al paciente primero."`
4. Restore the patient first (POST `/patients/{id}/restore`)
5. Now restore the diet — should succeed with `{"ok": true}`

- [ ] **Step 4: Commit**

```bash
git add backend/app/api/diets.py
git commit -m "feat: block diet restore when patient is still soft-deleted"
```

---

### Task 2: Frontend — Show actual error message in trash restore

**Files:**
- Modify: `frontend/src/pages/Trash.tsx:83-84`

- [ ] **Step 1: Capture error message in catch block**

Change the catch in `handleRestore` from:

```tsx
    } catch {
      addToast("Error al restaurar", "error")
    }
```

To:

```tsx
    } catch (err) {
      addToast(err instanceof Error ? err.message : "Error al restaurar", "error")
    }
```

- [ ] **Step 2: TypeScript check**

Run: `cd frontend && npx tsc --noEmit --pretty`
Expected: No errors

- [ ] **Step 3: Test manually in browser**

1. Open the app, go to Papelera (Trash)
2. With a patient still in trash (not restored), click "Restaurar" on one of their diets
3. Expected: Toast shows `"No se puede restaurar la dieta porque el paciente está en la papelera. Restaure al paciente primero."`
4. Restore the patient first, then restore the diet
5. Expected: Toast shows `"Dieta restaurada exitosamente"`

- [ ] **Step 4: Commit**

```bash
git add frontend/src/pages/Trash.tsx
git commit -m "fix: show backend error message when diet restore fails"
```
