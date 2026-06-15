# Soft Delete / Papelera + Compartir Formulario con Web Share API

**Date:** 2026-06-15
**Status:** Design approved, ready for implementation plan

## Context

Dos funcionalidades independientes que mejoran la gestión de datos y la experiencia móvil:

1. **Soft Delete + Papelera**: No existe forma de eliminar pacientes ni dietas. Solo se pueden archivar pacientes o descartar dietas. Se necesita un sistema de eliminación suave (soft delete) con una papelera donde la doctora pueda restaurar o eliminar permanentemente.
2. **Compartir formulario con Web Share API**: Actualmente los links de formulario solo se comparten vía WhatsApp/Correo fijo. Se necesita el mismo comportamiento que el PDF: en móvil usar `navigator.share()` para abrir el menú nativo del SO.

---

## Feature 1: Soft Delete + Papelera

### Modelo de datos

Agregar columna `deleted_at` (datetime, nullable) a las tablas `patients` y `diets`:

```python
# backend/app/models.py
class Patient(Base):
    __tablename__ = "patients"
    # ... existing columns ...
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, default=None)

class Diet(Base):
    __tablename__ = "diets"
    # ... existing columns ...
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, default=None)
```

- `is_archived` e `is_active` se mantienen en Patient — ahora con significado independiente del soft delete
- Cuando `deleted_at IS NOT NULL` → el registro está en la papelera
- Cuando se restaura → `deleted_at = NULL`

### Endpoints backend

| Método | Ruta | Comportamiento |
|--------|------|---------------|
| `POST` | `/patients/{id}/soft-delete` | Setea `deleted_at = now()` en el paciente y todas sus dietas asociadas |
| `POST` | `/diets/{id}/soft-delete` | Setea `deleted_at = now()` en la dieta |
| `POST` | `/patients/{id}/restore` | Setea `deleted_at = NULL` en paciente y sus dietas |
| `POST` | `/diets/{id}/restore` | Setea `deleted_at = NULL` en dieta |
| `DELETE` | `/patients/{id}/hard-delete` | Elimina permanentemente paciente + perfil + métricas + dietas asociadas |
| `DELETE` | `/diets/{id}/hard-delete` | Elimina permanentemente la dieta + versiones |
| `GET` | `/trash/patients` | Lista pacientes con `deleted_at IS NOT NULL` (paginated) |
| `GET` | `/trash/diets` | Lista dietas con `deleted_at IS NOT NULL` (paginated) |

### Filtros en endpoints existentes

- `GET /patients` — agregar condición `AND deleted_at IS NULL` para no mostrar pacientes eliminados
- `GET /diets` — agregar condición `AND deleted_at IS NULL` para no mostrar dietas eliminadas
- `GET /patients/{id}` — permitir acceso aunque tenga `deleted_at` (para poder restaurar desde papelera)
- `POST /diets/generate` — verificar que el paciente no tenga `deleted_at`

### Frontend: nueva página /trash

**Nuevo archivo:** `frontend/src/pages/Trash.tsx`
- Ruta: `/trash` (protegida con RequireAuth)
- Dos pestañas: "🧑 Pacientes" y "📋 Dietas"
- Barra de búsqueda por nombre
- Lista con: nombre, fecha de eliminación, acciones (Restaurar / Eliminar permanentemente)
- Botón "Eliminar permanentemente" → confirmación tipo "¿Estás seguro? Esta acción no se puede deshacer"
- Auto-limpieza: elementos con más de 30 días de antigüedad se pueden eliminar en批量

**Sidebar/navegación:** Agregar enlace a "🗑️ Papelera" en `AdminLayout.tsx`

**Opciones de eliminación en vistas normales:**
- `PatientRow.tsx` — agregar opción "🗑️ Eliminar" en el menú de acciones por paciente
- `Diets.tsx` — agregar botón "🗑️" por fila de dieta, o menú de acción

**Confirmación:** Modal simple: "¿Eliminar [nombre]? Se moverá a la papelera. Podrás restaurarlo dentro de 30 días."

### API Frontend

Agregar a `frontend/src/services/api.ts`:
- `softDeletePatient(id)`, `softDeleteDiet(id)`
- `restorePatient(id)`, `restoreDiet(id)`
- `hardDeletePatient(id)`, `hardDeleteDiet(id)`
- `getTrashPatients(params)`, `getTrashDiets(params)`

---

## Feature 2: Compartir Formulario con Web Share API

### Cambios en ShareModal.tsx

Reemplazar los botones fijos de WhatsApp/Correo por:
- Botón "📋 Copiar" (siempre visible)
- Botón "📤 Compartir" (visible en móvil con soporte Web Share API)

**Lógica de `navigator.share`:**
```ts
const url = "https://nutribot.app/intake/abc123";
if (navigator.share) {
  await navigator.share({
    title: "Completa tu ficha nutricional - Dra. Acosta",
    text: "La Dra. Acosta te invita a completar tu ficha nutricional:",
    url: url,
  });
}
```

**En desktop** (sin `navigator.share`): mostrar los botones actuales (WhatsApp, Correo, Copiar) como fallback.

### Remover share de Patients.tsx

- Eliminar el botón "Enviar formulario" del menú de `PatientRow.tsx`
- Eliminar el `onShare` prop de `Patients.tsx` → `PatientRow`
- El sharing de formularios solo se hace desde `IntakeLinks.tsx`

### Dónde se comparten

| Página | Visibilidad del share |
|--------|-----------------------|
| IntakeLinks.tsx (al crear link) | ✅ Web Share API en móvil, WhatsApp/Correo/Copiar en desktop |
| Patients.tsx (lista de pacientes) | ❌ Eliminar completamente |

---

## Archivos a crear

| Archivo | Propósito |
|---------|-----------|
| `frontend/src/pages/Trash.tsx` | Papelera con pestañas Pacientes/Dietas |
| (ninguno en backend — se modificarán los existentes) | |

## Archivos a modificar

| Archivo | Cambios |
|---------|---------|
| `backend/app/models.py` | Agregar `deleted_at` a Patient y Diet |
| `backend/app/schemas.py` | Agregar esquemas TrashPatientOut, TrashDietOut |
| `backend/app/api/trash.py` | **Nuevo router** con endpoints de papelera |
| `backend/app/api/patients.py` | Agregar DELETE /{id} + POST /{id}/restore. Filtrar `deleted_at IS NULL` en GET /patients |
| `backend/app/api/diets.py` | Agregar DELETE /{id} + POST /{id}/restore. Filtrar `deleted_at IS NULL` en GET /diets |
| `backend/app/api/router.py` | Montar trash router |
| `backend/app/logic/diet_eligibility.py` | Agregar chequeo de `deleted_at` del paciente |
| `backend/app/services/diet_service.py` | Verificar `deleted_at` en create_new_diet |
| `backend/app/api/admin.py` | (opcional) Permitir a admin ver papelera |
| `frontend/src/services/api.ts` | Agregar funciones de soft/hard delete + trash + restore |
| `frontend/src/pages/Trash.tsx` | Nueva página de papelera |
| `frontend/src/pages/Patients.tsx` | Agregar opción "Eliminar" en pacientes |
| `frontend/src/pages/Diets.tsx` | Agregar opción "Eliminar" en dietas |
| `frontend/src/components/patients/PatientRow.tsx` | Agregar "🗑️ Eliminar" al menú de acciones |
| `frontend/src/layouts/AdminLayout.tsx` | Agregar enlace "🗑️ Papelera" en la sidebar |
| `frontend/src/App.tsx` | Agregar ruta `/trash` |
| `frontend/src/components/sharing/ShareModal.tsx` | Web Share API + fallback desktop |
| `frontend/src/components/ShareButtons.tsx` | Refactor para usar Web Share o eliminar si no se usa |
| `backend/alembic/versions/` | **Nueva migración** agregando columna `deleted_at` |

## Migración de Base de Datos

```sql
ALTER TABLE patients ADD COLUMN deleted_at TIMESTAMPTZ;
ALTER TABLE diets ADD COLUMN deleted_at TIMESTAMPTZ;
```

Generar con `alembic revision --autogenerate -m "add deleted_at for soft delete"`

## Verificación

1. **Soft delete paciente**: Ir a Patients → eliminar paciente → aparece en papelera → desaparece de lista normal
2. **Restaurar**: Ir a papelera → restaurar → paciente vuelve a lista normal
3. **Hard delete**: Ir a papelera → eliminar permanentemente → registro borrado de DB
4. **Cascada**: Eliminar paciente → todas sus dietas también tienen `deleted_at`
5. **Dietas**: Eliminar dieta desde Diets.tsx → aparece en pestaña Dietas de papelera
6. **Compartir formulario móvil**: Crear link → tocar "Compartir" → menú nativo del SO
7. **Compartir formulario desktop**: Crear link → mostrar Copiar + WhatsApp + Correo
8. **Compartir eliminado de Patients**: No hay botón compartir en lista de pacientes
9. **Build**: `npx tsc --noEmit && npm run build` sin errores
