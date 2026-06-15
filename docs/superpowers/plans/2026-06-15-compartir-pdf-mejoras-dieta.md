# Compartir PDF + Duración + Reglas Clínicas — Plan

> **For agentic workers:** Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans.

**Goal:** Add mobile PDF sharing via Web Share API, emerald selected-state feedback on duration buttons, and human-readable clinical rule labels.

**Architecture:** Three independent frontend-only changes: (1) Extract blob fetch from downloadDietPdf, add `onSharePdf` prop through DietDetail → DietPreviewPanel → DietActions, show share button on mobile. (2) Add `value` prop to DurationPresetButtons with Tailwind emerald classes. (3) Add rule-code-to-label mapping in DietPreviewPanel.

**Tech Stack:** React 19, TypeScript, Tailwind CSS v4, Web Share API

**Spec:** `docs/superpowers/specs/2026-06-15-compartir-pdf-mejoras-dieta.md`

---

### Task 1: Extract getDietPdfBlob + add share button in DietActions

**Files:**
- Modify: `frontend/src/services/api.ts:390-405`
- Modify: `frontend/src/components/diet/DietActions.tsx`
- Modify: `frontend/src/components/diet/DietPreviewPanel.tsx:6-15,64-80`
- Modify: `frontend/src/pages/DietDetail.tsx:3,38-48,144`

- [ ] **Step 1: Extract `getDietPdfBlob` from `downloadDietPdf` in api.ts**

Replace lines 390-405 with:

```typescript
export async function getDietPdfBlob(id: number): Promise<Blob> {
  const token = getStoredToken()
  const res = await fetch(`${API_BASE_URL}/diets/${id}/pdf`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  })
  if (!res.ok) {
    throw new Error(await readApiError(res))
  }
  return res.blob()
}

export async function downloadDietPdf(id: number) {
  const blob = await getDietPdfBlob(id)
  const url = URL.createObjectURL(blob)
  const a = document.createElement("a")
  a.href = url
  a.download = `diet-${id}.pdf`
  a.click()
  URL.revokeObjectURL(url)
}
```

- [ ] **Step 2: Add `onSharePdf` prop and share button to DietActions.tsx**

Add `onSharePdf` to the Props type and add share button in the "generated" status block:

```tsx
import { PencilSimple, Share } from "@phosphor-icons/react"
import Button from "../ui/Button"
import QuickAdjustMenu from "./QuickAdjustMenu"
import { useState } from "react"

type Props = {
  dietId: number
  status: string
  onApprove: () => void
  onDiscard: () => void
  onQuickAdjust: (key: string, label: string) => void
  onDownloadPdf: () => void
  onSharePdf?: () => void
  onToggleEdit?: () => void
  editing?: boolean
  loading: boolean
}

export default function DietActions({
  dietId,
  status,
  onApprove,
  onDiscard,
  onQuickAdjust,
  onDownloadPdf,
  onSharePdf,
  onToggleEdit,
  editing,
  loading,
}: Props) {
  const [showQuickAdjust, setShowQuickAdjust] = useState(false)
  const isEditable = status === "pending_approval" || status === "generated"

  // ... keep the "pending_approval" block unchanged ...

  if (status === "generated") {
    return (
      <div className="space-y-2">
        <Button onClick={onDownloadPdf} className="w-full">
          📄 Descargar PDF
        </Button>
        {onSharePdf && (
          <Button
            variant="secondary"
            onClick={onSharePdf}
            className="w-full border-emerald-500 text-emerald-700 hover:bg-emerald-50"
          >
            <span className="flex items-center justify-center gap-1.5">
              <Share size={14} />
              Compartir PDF
            </span>
          </Button>
        )}
        <Button variant="ghost" onClick={onToggleEdit} className="w-full text-sm">
          <span className="flex items-center justify-center gap-1.5">
            <PencilSimple size={14} />
            {editing ? "Dejar de editar" : "Editar comidas"}
          </span>
        </Button>
      </div>
    )
  }

  return null
}
```

- [ ] **Step 3: Wire `onSharePdf` through DietPreviewPanel.tsx**

Add `onSharePdf` to Props type (line 6-15):
```tsx
type Props = {
  diet: Diet
  editable?: boolean
  onMealSave?: (dayIndex: number, slotKey: string, text: string) => void
  onToggleEdit?: () => void
  onApprove?: () => void
  onDiscard?: () => void
  onDownloadPdf?: () => void
  onSharePdf?: () => void
}
```

In the function signature:
```tsx
export default function DietPreviewPanel({ diet, editable, onMealSave, onToggleEdit, onApprove, onDiscard, onDownloadPdf, onSharePdf }: Props) {
```

In the `<DietActions>` call (around line 64), add `onSharePdf`:
```tsx
<DietActions
  dietId={diet.id}
  status={diet.status}
  onApprove={onApprove || (() => approve.mutate(diet.id))}
  onDiscard={onDiscard || (() => discard.mutate(diet.id))}
  onQuickAdjust={(key, label) => quickAdjust.mutate({ dietId: diet.id, adjustment: label })}
  onDownloadPdf={() => {
    if (onDownloadPdf) {
      onDownloadPdf()
    } else {
      import("../../services/api").then(({ downloadDietPdf }) => downloadDietPdf(diet.id))
    }
  }}
  onSharePdf={onSharePdf}
  onToggleEdit={onToggleEdit}
  editing={editable}
  loading={loading}
/>
```

- [ ] **Step 4: Add `handleSharePdf` in DietDetail.tsx**

Import `getDietPdfBlob` at line 3:
```tsx
import { downloadDietPdf, getDiet, getDietPdfBlob } from "../services/api"
```

Add `handleSharePdf` after `handleDownloadPdf` (after line 48):
```tsx
const handleSharePdf = async () => {
  if (!diet) return
  setPdfLoading(true)
  try {
    const blob = await getDietPdfBlob(diet.id)
    const file = new File([blob], `dieta-${diet.id}.pdf`, { type: "application/pdf" })
    if (navigator.share && navigator.canShare({ files: [file] })) {
      await navigator.share({
        files: [file],
        title: `Dieta - ${diet.title || "Plan Nutricional"}`,
      })
    } else {
      // Fallback: download if Web Share API doesn't support files
      const url = URL.createObjectURL(blob)
      const a = document.createElement("a")
      a.href = url
      a.download = `dieta-${diet.id}.pdf`
      a.click()
      URL.revokeObjectURL(url)
    }
  } catch (err: unknown) {
    if (err instanceof DOMException && err.name === "AbortError") {
      // User cancelled the share dialog — not an error
      return
    }
    addToast(err instanceof Error ? err.message : "Error al compartir PDF", "error")
  } finally {
    setPdfLoading(false)
  }
}
```

Pass it to DietPreviewPanel (around line 144):
```tsx
<DietPreviewPanel
  diet={diet}
  editable={editing}
  onMealSave={editing ? handleMealSave : undefined}
  onToggleEdit={handleToggleEdit}
  onDownloadPdf={handleDownloadPdf}
  onSharePdf={handleSharePdf}
/>
```

- [ ] **Step 5: Verify TypeScript compilation**

```bash
cd frontend && npx tsc --noEmit
```

Expected: no new TS errors.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/services/api.ts frontend/src/components/diet/DietActions.tsx frontend/src/components/diet/DietPreviewPanel.tsx frontend/src/pages/DietDetail.tsx
git commit -m "feat: add PDF sharing via Web Share API on mobile + keep download on desktop"
```

---

### Task 2: DurationPresetButtons with emerald selected state

**Files:**
- Modify: `frontend/src/components/DurationPresetButtons.tsx`
- Modify: `frontend/src/pages/Diets.tsx:310-313`

- [ ] **Step 1: Add `value` prop and Tailwind styling to DurationPresetButtons.tsx**

Full replacement:

```tsx
type Props = {
  presets: readonly number[]
  value?: number
  onSelect: (days: number) => void
}

export function DurationPresetButtons({ presets, value, onSelect }: Props) {
  return (
    <div className="mb-2">
      <span className="text-xs text-slate-500 block mb-1.5">
        Quick (days)
      </span>
      <div className="flex flex-wrap gap-2">
        {presets.map((d) => {
          const selected = value === d
          return (
            <button
              key={d}
              type="button"
              onClick={() => onSelect(d)}
              className={`rounded-lg border px-3 py-1 text-sm font-medium transition-colors ${
                selected
                  ? "border-emerald-500 bg-emerald-50 text-emerald-700 shadow-sm"
                  : "border-gray-200 bg-white text-gray-600 hover:bg-gray-50"
              }`}
            >
              {d}
            </button>
          )
        })}
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Pass `value` from Diets.tsx**

In Diets.tsx line 310-313, add `value`:
```tsx
<DurationPresetButtons
  presets={durationPresets}
  value={Number(genDuration) || undefined}
  onSelect={(d) => setGenDuration(String(d))}
/>
```

- [ ] **Step 3: Verify TypeScript compilation**

```bash
cd frontend && npx tsc --noEmit
```

Expected: no new TS errors.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/DurationPresetButtons.tsx frontend/src/pages/Diets.tsx
git commit -m "feat: add emerald selected-state feedback to DurationPresetButtons"
```

---

### Task 3: Clinical rules — human-friendly labels

**Files:**
- Modify: `frontend/src/components/diet/DietPreviewPanel.tsx:50-58`

- [ ] **Step 1: Add rules mapping and update rendering in DietPreviewPanel.tsx**

Replace lines 50-58 (the clinical rules block) with:

```tsx
{/* Clinical rules — human-readable labels */}
{Array.isArray(plan.clinical_rules_applied) && plan.clinical_rules_applied.length > 0 && (
  <div className="rounded-lg border border-emerald-200 bg-emerald-50/50 p-3">
    <p className="text-xs font-semibold text-emerald-800 mb-2">
      🧬 Reglas clínicas aplicadas:
    </p>
    <div className="space-y-1.5">
      {(plan.clinical_rules_applied as string[]).map((r) => (
        <p key={r} className="text-xs text-emerald-700">
          {CLINICAL_RULE_LABELS[r] || `• ${r}`}
        </p>
      ))}
    </div>
  </div>
)}
```

Add the mapping constant at the top of the file (after imports, before the component):

```tsx
const CLINICAL_RULE_LABELS: Record<string, string> = {
  diabetes_carb_distribution_low_gi:
    "🩸 Diabetes: Distribución de carbohidratos en comidas, priorizando bajo índice glucémico",
  hypertension_sodium_moderation:
    "❤️ Hipertensión: Moderación de sodio, patrón tipo DASH",
  renal_protein_ceiling_applied:
    "🫘 Condición renal: Tope conservador de proteína — individualizar con nefrología",
  dyslipidemia_reduced_fat_fraction:
    "🩺 Dislipidemia: Límite de grasas saturadas y trans, favorecer grasas insaturadas y fibra",
}
```

- [ ] **Step 2: Verify TypeScript compilation**

```bash
cd frontend && npx tsc --noEmit
```

Expected: no new TS errors.

- [ ] **Step 3: Build check**

```bash
cd frontend && npm run build
```

Expected: build succeeds.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/diet/DietPreviewPanel.tsx
git commit -m "feat: replace technical clinical rule codes with human-friendly Spanish labels"
```

---

## Verification Summary

| # | What to check | How |
|---|---------------|-----|
| 1 | `npx tsc --noEmit` passes | Terminal |
| 2 | `npm run build` succeeds | Terminal |
| 3 | Share button visible on mobile, calls native share sheet | Browser dev tools mobile mode |
| 4 | Share button NOT visible on desktop | Normal browser |
| 5 | Duration button turns emerald green when selected | Click 14 días → button gets border-emerald-500 bg-emerald-50 |
| 6 | Clinical rules show friendly labels with emoji icons | Open diet detail for patient with conditions |
| 7 | Unknown rule codes fall back to raw display | (test by temporarily removing a key from the mapping) |
