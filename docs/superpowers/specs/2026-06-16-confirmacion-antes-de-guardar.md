# Confirmación antes de guardar — Modal de revisión

**Fecha:** 2026-06-16
**Estado:** Design approved

---

## Resumen

Agregar un modal de confirmación antes de ejecutar cualquier guardado, tanto para el doctor (en PatientDetail) como para el paciente (en PublicIntake register y update). El modal muestra un resumen de los cambios detectados y requiere confirmación explícita.

---

## Componentes

### ConfirmModal (nuevo)

Componente reutilizable que recibe:

```tsx
interface ConfirmModalProps {
  open: boolean
  onClose: () => void      // "Corregir" / "Continuar editando"
  onConfirm: () => void    // "Confirmar" — ejecuta el guardado real
  title: string            // "Revisa tus datos" / "Revisar cambios"
  changes: ChangeItem[]    // lista de cambios a mostrar
}

interface ChangeItem {
  label: string     // "Peso", "País", "Nombre"...
  oldValue?: string // valor anterior (tachado)
  newValue: string  // valor nuevo (en negrita)
  isNew?: boolean   // true si es un valor nuevo sin comparación
}
```

### Botones

- **"Confirmar"** → verde, ejecuta `onConfirm()`, cierra el modal
- **"Corregir"** / **"Continuar editando"** → blanco con borde, ejecuta `onClose()`, vuelve al formulario

---

## Flujos

### 1. Doctor edita perfil clínico (PatientDetail)

```
Usuario modifica campos → Click "Guardar"
  → Capturar estado actual de los campos editados
  → Comparar con valores originales (snapshot al abrir)
  → Si hay diferencias: abrir ConfirmModal con cambios
    → "Confirmar": ejecuta patch_profile/put_profile real
    → "Continuar editando": cierra modal, datos intactos
  → Si no hay diferencias: toast "Sin cambios que guardar"
```

### 2. Paciente se registra (PublicIntake — register)

```
Usuario llena formulario → Click "Enviar registro"
  → Validar campos requeridos
  → Abrir ConfirmModal con resumen de TODOS los datos
  → "Confirmar y enviar": ejecuta submitIntakeForm
  → "Corregir": cierra modal, formulario intacto
```

### 3. Paciente actualiza (PublicIntake — update)

```
Usuario modifica campos → Click "Actualizar datos"
  → Capturar estado actual
  → Comparar con valores originales (fetch inicial)
  → Si hay diferencias: abrir ConfirmModal
    → "Confirmar": ejecuta updateIntakeForm
    → "Corregir": cierra modal
  → Si no hay diferencias: toast "Sin cambios"
```

---

## Archivos a modificar

| Archivo | Cambio |
|---------|--------|
| `frontend/src/components/ui/ConfirmModal.tsx` | **Nuevo** — componente genérico |
| `frontend/src/pages/PatientDetail.tsx` | Interceptar `onSaveProfile`, `onSaveData` con modal |
| `frontend/src/pages/PublicIntake.tsx` | Interceptar `onSubmit` (register + update) con modal |

---

## No-Alcance

- No se modifica el backend (API calls idénticas)
- No se modifican validaciones existentes
- No se agrega lógica de "deshacer" después de confirmar
- No se cambia el diseño de los formularios existentes
