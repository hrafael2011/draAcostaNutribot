# Confirmación antes de guardar — Plan de Implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Agregar modal de confirmación antes de guardar en PatientDetail (doctor) y PublicIntake (paciente).

**Architecture:** Componente `ConfirmModal` genérico reutilizado en 3 flujos. Backend no se modifica. El modal captura el estado actual del formulario, lo compara con los valores originales, y muestra las diferencias antes de ejecutar la API call.

**Tech Stack:** React + Tailwind, framer-motion (ya instalado)

**Spec:** `docs/superpowers/specs/2026-06-16-confirmacion-antes-de-guardar.md`

---

### Task 1: Crear ConfirmModal component

**Files:**
- Create: `frontend/src/components/ui/ConfirmModal.tsx`

Componente reutilizable para los 3 flujos.

- [ ] **Step 1: Crear ConfirmModal.tsx**

```tsx
import { AnimatePresence, motion } from "framer-motion"
import { Check, PencilSimple } from "@phosphor-icons/react"

export interface ChangeItem {
  label: string
  oldValue?: string
  newValue: string
  isNew?: boolean
}

interface ConfirmModalProps {
  open: boolean
  title: string
  description?: string
  changes: ChangeItem[]
  onConfirm: () => void
  onEdit: () => void
  confirmLabel?: string
  editLabel?: string
  loading?: boolean
}

export default function ConfirmModal({
  open,
  title,
  description,
  changes,
  onConfirm,
  onEdit,
  confirmLabel = "Confirmar",
  editLabel = "Corregir",
  loading = false,
}: ConfirmModalProps) {
  return (
    <AnimatePresence>
      {open && (
        <motion.div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/20 backdrop-blur-sm"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
        >
          <motion.div
            className="w-full max-w-md mx-4 bg-white rounded-2xl shadow-xl"
            initial={{ opacity: 0, y: 16, scale: 0.96 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 16, scale: 0.96 }}
          >
            <div className="px-6 pt-6 pb-4">
              <h2 className="text-lg font-semibold text-gray-900">{title}</h2>
              {description && (
                <p className="text-sm text-gray-500 mt-1">{description}</p>
              )}
            </div>

            <div className="px-6 pb-4">
              <div className="rounded-xl bg-emerald-50 border border-emerald-200 p-4">
                {changes.length === 0 ? (
                  <p className="text-sm text-emerald-700 text-center">Sin cambios detectados</p>
                ) : (
                  <div className="space-y-2">
                    {changes.map((change, i) => (
                      <div key={i} className="flex justify-between items-center text-sm">
                        <span className="text-gray-500">{change.label}</span>
                        <div className="text-right">
                          {change.isNew ? (
                            <span className="font-medium text-emerald-700">{change.newValue}</span>
                          ) : (
                            <>
                              {change.oldValue && (
                                <span className="text-gray-400 line-through text-xs mr-1">
                                  {change.oldValue}
                                </span>
                              )}
                              <span className="font-medium text-gray-800">→ {change.newValue}</span>
                            </>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            <div className="px-6 pb-6 flex gap-3">
              <button
                type="button"
                onClick={onEdit}
                disabled={loading}
                className="flex-1 flex items-center justify-center gap-2 rounded-xl border border-gray-300 px-4 py-3 text-sm font-semibold text-gray-700 hover:bg-gray-50 disabled:opacity-50 transition-colors"
              >
                <PencilSimple size={18} />
                {editLabel}
              </button>
              <button
                type="button"
                onClick={onConfirm}
                disabled={loading || changes.length === 0}
                className="flex-1 flex items-center justify-center gap-2 rounded-xl bg-emerald-600 px-4 py-3 text-sm font-semibold text-white hover:bg-emerald-700 disabled:opacity-50 transition-colors"
              >
                <Check size={18} weight="bold" />
                {loading ? "Guardando..." : confirmLabel}
              </button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
```

- [ ] **Step 2: Verificar TypeScript**

```bash
cd /home/hendrick-rafael/Desktop/Proyectos Oficiales/diet_telegram_agent/frontend && npx tsc --noEmit --pretty 2>&1 | head -10
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/ui/ConfirmModal.tsx
git commit -m "feat: add ConfirmModal component for review-before-save"
```

---

### Task 2: Integrar modal en guardado del doctor (PatientDetail)

**Files:**
- Modify: `frontend/src/pages/PatientDetail.tsx`

Interceptar `onSaveProfile` para abrir el modal con los cambios detectados antes de llamar a la API.

- [ ] **Step 1: Agregar estado del modal**

Agregar al inicio del componente (junto a los otros estados):
```tsx
const [confirmModal, setConfirmModal] = useState<{
  open: boolean
  changes: ChangeItem[]
  onConfirm: () => void
}>({ open: false, changes: [], onConfirm: () => {} })
```

- [ ] **Step 2: Importar ConfirmModal y ChangeItem**

Agregar al import:
```tsx
import ConfirmModal from "../components/ui/ConfirmModal"
import type { ChangeItem } from "../components/ui/ConfirmModal"
```

- [ ] **Step 3: Modificar onSaveProfile para abrir modal**

Localizar `onSaveProfile` (alrededor de línea 1000). Reemplazar el cuerpo actual con:

```tsx
const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    // Construir los cambios detectados
    const changes: ChangeItem[] = []
    const data = profilePatch.model_dump(exclude_unset=True)
    for (const [key, value] of Object.entries(data)) {
      const label = profileLabels[key as keyof typeof profileLabels] || key
      const oldVal = originalProfile?.[key as keyof PatientProfile]
      const oldStr = oldVal != null && oldVal !== "" ? String(oldVal) : undefined
      const newStr = String(value)
      if (oldStr !== newStr) {
        changes.push({ label, oldValue: oldStr, newValue: newStr })
      }
    }
    if (changes.length === 0) {
      addToast("Sin cambios que guardar", "info")
      return
    }
    // Abrir modal, no enviar aún
    setConfirmModal({
      open: true,
      changes,
      onConfirm: async () => {
        try {
          await patchProfile(patientId, data)
          addToast("Perfil clínico guardado", "success")
          profileMutation.mutate()
        } catch (err) {
          addToast(err instanceof Error ? err.message : "Error al guardar", "error")
        } finally {
          setConfirmModal({ open: false, changes: [], onConfirm: () => {} })
        }
      },
    })
  }
```

NOTA: El `profileLabels` es un diccionario que mapea nombres de campo a etiquetas legibles. Agregarlo:
```tsx
const profileLabels: Record<string, string> = {
  objective: "Objetivo",
  diseases: "Enfermedades",
  medications: "Medicamentos",
  food_allergies: "Alergias alimentarias",
  foods_avoided: "Alimentos a evitar",
  medical_history: "Historial médico",
  dietary_style: "Estilo de alimentación",
  food_preferences: "Alimentos que le gustan",
  disliked_foods: "Alimentos que NO le gustan",
  water_intake_liters: "Agua (L/día)",
  activity_level: "Actividad física",
  stress_level: "Estrés",
  sleep_quality: "Calidad del sueño",
  sleep_hours: "Horas de sueño",
  budget_level: "Presupuesto",
  adherence_level: "Adherencia",
  exercise_frequency_per_week: "Ejercicio (días/sem)",
  exercise_type: "Tipo de ejercicio",
  extra_notes: "Notas adicionales",
  weight_kg: "Peso",
  height_cm: "Altura",
  neck_cm: "Cuello",
  chest_cm: "Pecho",
  waist_cm: "Cintura",
  hip_cm: "Cadera",
  leg_cm: "Pierna",
  calf_cm: "Pantorrilla",
  first_name: "Nombre",
  last_name: "Apellido",
  whatsapp: "WhatsApp",
  country: "País",
  city: "Ciudad",
}
```

- [ ] **Step 4: Renderizar ConfirmModal**

Agregar antes del cierre del componente principal (`</div>`, `</>`):
```tsx
<ConfirmModal
  open={confirmModal.open}
  title="Revisar cambios"
  description="Confirma los cambios que realizaste en el perfil del paciente."
  changes={confirmModal.changes}
  onConfirm={confirmModal.onConfirm}
  onEdit={() => setConfirmModal({ open: false, changes: [], onConfirm: () => {} })}
  confirmLabel="Confirmar cambios"
  editLabel="Continuar editando"
/>
```

- [ ] **Step 5: Verificar TypeScript**

```bash
cd frontend && npx tsc --noEmit --pretty 2>&1 | head -10
```

- [ ] **Step 6: Commit**

```bash
git add frontend/src/pages/PatientDetail.tsx
git commit -m "feat: add confirmation modal before saving patient profile"
```

---

### Task 3: Integrar modal en registro de paciente (PublicIntake register)

**Files:**
- Modify: `frontend/src/pages/PublicIntake.tsx`

Interceptar el submit del registro para mostrar modal de resumen antes de enviar.

- [ ] **Step 1: Agregar import y estado**

```tsx
import ConfirmModal from "../components/ui/ConfirmModal"
import type { ChangeItem } from "../components/ui/ConfirmModal"

// Estado dentro del componente
const [confirmOpen, setConfirmOpen] = useState(false)
const [confirmChanges, setConfirmChanges] = useState<ChangeItem[]>([])
const [confirmLoading, setConfirmLoading] = useState(false)
```

- [ ] **Step 2: Modificar onSubmit para register**

En el bloque de registro (donde se construye `body`), reemplazar el `try { await submitIntakeForm... }` con:

```tsx
    // En vez de enviar directo, mostrar modal de confirmación
    const changes: ChangeItem[] = [
      { label: "Nombre", newValue: `${str("first_name")} ${str("last_name")}`, isNew: true },
      { label: "Fecha de nacimiento", newValue: birthDate, isNew: true },
      { label: "Sexo", newValue: str("sex"), isNew: true },
      { label: "País", newValue: country, isNew: true },
      { label: "Ciudad", newValue: city, isNew: true },
      { label: "Objetivo", newValue: objective, isNew: true },
    ]
    if (str("whatsapp")) changes.push({ label: "WhatsApp", newValue: str("whatsapp"), isNew: true })
    if (str("email")) changes.push({ label: "Email", newValue: str("email"), isNew: true })
    if (str("disliked_foods")) changes.push({ label: "Alimentos que no le gustan", newValue: str("disliked_foods"), isNew: true })

    setConfirmChanges(changes)
    setConfirmOpen(true)
    return // no enviar aún — el modal decide
```

- [ ] **Step 3: Agregar handler de confirmación**

```tsx
  async function handleRegisterConfirm() {
    setConfirmLoading(true)
    try {
      const body = buildRegisterBody() // extraer la lógica de construcción del body a una función
      await submitIntakeForm(token, body)
      setDone(true)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Submit failed")
    } finally {
      setConfirmLoading(false)
      setConfirmOpen(false)
    }
  }
```

NOTA: La función `buildRegisterBody()` debe extraerse del `onSubmit` actual para que tanto el modal como el submit original usen la misma lógica. O más simple: almacenar `body` en una ref/state al mostrar el modal.

- [ ] **Step 4: Renderizar ConfirmModal**

Agregar antes del cierre del componente:
```tsx
<ConfirmModal
  open={confirmOpen}
  title="Revisa tus datos"
  description="Confirmá que toda tu información sea correcta antes de enviarla."
  changes={confirmChanges}
  onConfirm={handleRegisterConfirm}
  onEdit={() => setConfirmOpen(false)}
  confirmLabel="Confirmar y enviar"
  editLabel="Corregir"
  loading={confirmLoading}
/>
```

- [ ] **Step 5: Verificar TypeScript**

```bash
cd frontend && npx tsc --noEmit --pretty 2>&1 | head -10
```

- [ ] **Step 6: Commit**

```bash
git add frontend/src/pages/PublicIntake.tsx
git commit -m "feat: add confirmation modal before patient registration"
```

---

### Task 4: Integrar modal en actualización de paciente (PublicIntake update)

**Files:**
- Modify: `frontend/src/pages/PublicIntake.tsx`

Misma lógica que register pero comparando valores viejos vs nuevos.

- [ ] **Step 1: Guardar valores originales**

Al cargar los datos del paciente en update mode, guardar snapshot:
```tsx
const [originalData, setOriginalData] = useState<Record<string, string> | null>(null)
```

En el `useEffect` de validación, cuando el meta tiene `patient_first_name`, guardar:
```tsx
if (m.link_type === "update" && m.patient_first_name) {
  setOriginalData({
    first_name: m.patient_first_name || "",
    last_name: m.patient_last_name || "",
  })
}
```

- [ ] **Step 2: Modificar onSubmit para update**

En el bloque de update, reemplazar `try { await updateIntakeForm... }` con:

```tsx
    // Detectar cambios
    const changes: ChangeItem[] = []
    const track = (label: string, key: string, current: string) => {
      const old = originalData?.[key] ?? ""
      if (current !== old) {
        changes.push({ label, oldValue: old || undefined, newValue: current })
      }
    }
    const firstName = str("first_name")
    const lastName = str("last_name")
    if (firstName) track("Nombre", "first_name", firstName)
    if (lastName) track("Apellido", "last_name", lastName)
    if (country && country !== originalData?.country) {
      changes.push({ label: "País", oldValue: originalData?.country, newValue: country })
    }
    if (city && city !== originalData?.city) {
      changes.push({ label: "Ciudad", oldValue: originalData?.city, newValue: city })
    }
    if (Number.isFinite(weight_kg)) {
      changes.push({ label: "Peso", oldValue: originalData?.weight_kg || undefined, newValue: String(weight_kg) })
    }

    if (changes.length === 0) {
      setError("No hay cambios para guardar")
      return
    }
    setConfirmChanges(changes)
    setConfirmOpen(true)
    return
```

- [ ] **Step 3: Agregar handler de confirmación para update**

```tsx
  async function handleUpdateConfirm() {
    setConfirmLoading(true)
    try {
      const updateBody: Record<string, unknown> = {}
      const firstName = str("first_name")
      const lastName = str("last_name")
      if (firstName) updateBody.first_name = firstName
      if (lastName) updateBody.last_name = lastName
      if (str("whatsapp")) updateBody.whatsapp = optStr("whatsapp")
      if (country) updateBody.country = country
      if (city) updateBody.city = city
      if (Number.isFinite(weight_kg)) updateBody.weight_kg = weight_kg

      await updateIntakeForm(token, updateBody)
      setDone(true)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Update failed")
    } finally {
      setConfirmLoading(false)
      setConfirmOpen(false)
    }
  }
```

- [ ] **Step 4: Verificar TypeScript**

```bash
cd frontend && npx tsc --noEmit --pretty 2>&1 | head -10
```

- [ ] **Step 5: Commit**

```bash
git add frontend/src/pages/PublicIntake.tsx
git commit -m "feat: add confirmation modal before patient update"
```

---

### Task 5: Verificación general

```bash
cd /home/hendrick-rafael/Desktop/Proyectos Oficiales/diet_telegram_agent/frontend && npx tsc --noEmit --pretty
```

---

## Resumen de cambios

| Archivo | Cambio |
|---------|--------|
| `frontend/src/components/ui/ConfirmModal.tsx` | **Nuevo** — Componente genérico de confirmación |
| `frontend/src/pages/PatientDetail.tsx` | Interceptar `onSaveProfile` con modal de cambios |
| `frontend/src/pages/PublicIntake.tsx` | Interceptar register y update con modal de confirmación |
