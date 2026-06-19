# Diet Restore — Patient Validation

## Context

When a patient is soft-deleted, all their diets are also soft-deleted. When the patient is restored, all their diets are restored. However, the individual diet restore endpoint does not check whether the patient is still in the trash — leading to an inconsistent state where a restored diet belongs to a deleted patient.

## Change

### Backend: `restore_diet` validation

**File:** `backend/app/api/diets.py`
**Endpoint:** `POST /{diet_id}/restore`

After fetching the diet and verifying doctor ownership, query the associated patient. If the patient has `deleted_at` set (is in the trash), return a **409 Conflict** error with a clear message.

```
Patient deleted → HTTP 409 "No se puede restaurar la dieta porque el paciente está en la papelera. Restaure al paciente primero."
Patient active   → proceed as before (set diet.deleted_at = None)
```

### Frontend: Show backend error message

**File:** `frontend/src/pages/Trash.tsx`
**Function:** `handleRestore`

Change the catch block from a generic `"Error al restaurar"` to display the actual error message from the backend (`err.message`). Falls back to the generic message if the error isn't an `Error` instance.

## Files affected

| File | Lines |
|------|-------|
| `backend/app/api/diets.py` | +7 (patient query + validation + HTTPException) |
| `frontend/src/pages/Trash.tsx` | ~2 (catch block) |
