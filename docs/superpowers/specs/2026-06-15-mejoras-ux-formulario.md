# UX Form Improvements — Date Picker, Objectives, No Aplica, Units

**Date:** 2026-06-15
**Status:** Approved
**Branch:** dev-local

## Context

The patient registration and editing forms have 4 UX friction points that make data entry slow or confusing:

1. **Date of birth**: Native `<input type="date">` requires ~420 backward clicks to reach birth years from the 80s/90s.
2. **Objectives**: Inconsistent options across forms. "Bajar de peso" and "Subir de peso" are missing from PatientDrawer.
3. **Clinical fields**: No way to indicate "not applicable" for diseases, medications, allergies, foods avoided, or medical history — users must guess what to type.
4. **Measurement units**: Admin forms (PatientDrawer, PatientDetail) only accept kg/cm. No toggle for lb or ft/in, unlike PublicIntake which already has them.

## Design Decisions

### 1. Date Picker → `react-day-picker`

- **Library**: `react-day-picker` v9 (~15KB gzipped, tree-shakeable)
- **Why**: Built-in `captionLayout="dropdown"` provides month + year `<select>` dropdowns for instant navigation to any decade. No custom code needed for the year-jump feature.
- **New component**: `frontend/src/components/ui/DatePicker.tsx`
  - Wraps `DayPicker` with emerald theme via Tailwind CSS custom properties (`--rdp-accent-color: #10b981`)
  - Popover mode: click trigger → calendar popover → select date → close
  - Trigger shows formatted date (DD/MM/AAAA) or placeholder
  - Allows empty/clearable state (some patients may not know exact birth date)
- **Replaces** native `<input type="date">` in 3 locations:
  - `PublicIntake.tsx:192`
  - `PatientDrawer.tsx:285`
  - `PatientDetail.tsx:845`

### 2. Objectives → 7 Unified Options

**Constant definition** (to be placed in `frontend/src/types/index.ts` or a new `frontend/src/constants/objectives.ts`):

```ts
export const OBJECTIVE_OPTIONS = [
  { value: "", label: "Sin especificar" },
  { value: "lose_weight", label: "⬇️  Bajar de peso" },
  { value: "fat_loss", label: "🔥  Pérdida de grasa" },
  { value: "muscle_gain", label: "💪  Ganancia muscular" },
  { value: "gain_weight", label: "⬆️  Subir de peso" },
  { value: "maintenance", label: "⚖️  Mantenimiento" },
  { value: "health_improvement", label: "❤️  Mejora de salud" },
  { value: "sports_performance", label: "🏃  Rendimiento deportivo" },
] as const;
```

- **PatientDrawer.tsx**: Replace current 5-option select with the 8-option constant.
- **PatientDetail.tsx**: Replace current 4-option select with the 8-option constant (currently has "Bajar de peso", "Mantenimiento", "Ganar musculo", "Subir de peso" — will be replaced).
- **PublicIntake.tsx**: Change from free-text input to `<select>` using the same constant (currently a text input with placeholder "e.g. lose_weight").

### 3. "No Aplica" → `NoAplicaField` Component

**New component**: `frontend/src/components/ui/NoAplicaField.tsx`

Props:
- `label: string` — field label
- `value: string` — controlled text value
- `onChange: (value: string) => void` — value callback
- `placeholder?: string` — when active
- `naLabel?: string` — defaults to "No aplica"
- `type?: "textarea" | "input"` — defaults to "textarea"

Behavior:
- Checkbox unchecked → field is editable, value is user text
- Checkbox checked → field is disabled (grayed out), value internally set to "No aplica"
- When submitted: if checked, sends `"No aplica"` to backend (or empty string — backend treats both as "not specified")

**Applied to 5 fields** (currently `<textarea>` or `<input>`):

| Form | Fields |
|------|--------|
| PublicIntake | diseases, medications, food_allergies, foods_avoided, medical_history |
| PatientDrawer | diseases, medications, food_allergies, foods_avoided |
| PatientDetail | diseases, medications, food_allergies, foods_avoided |

### 4. Unit Toggles → `WeightInput` + `HeightInput` Components

**New components:**
- `frontend/src/components/ui/WeightInput.tsx` — number input + kg/lb toggle
- `frontend/src/components/ui/HeightInput.tsx` — number input(s) + cm ↔ ft/in toggle

**Conversion constants** (already exist in PublicIntake.tsx:14-15, extract to shared location):
```ts
export const WEIGHT_LB_TO_KG = 0.45359237;
export const IN_TO_CM = 2.54;
```

**Behavior:**
- Weight: single number input + unit `<select>` (kg | lb). On change, calls `onChange({ value: number, unit: "kg" | "lb" })`.
- Height: when cm → single number input. When ft/in → two number inputs (feet + inches). Calls `onChange({ valueCm: number })` always normalized to cm.
- The parent form receives normalized values (kg, cm) for submission — conversion happens inside the component.

**Applied in:**
- `PatientDrawer.tsx` — Metrics section (weight_kg, height_cm) → toggleable
- `PatientDetail.tsx` — Metrics form → toggleable
- `PublicIntake.tsx` — Already has toggles; refactor to reuse `WeightInput`/`HeightInput`

## Files to Create

| File | Purpose |
|------|---------|
| `frontend/src/components/ui/DatePicker.tsx` | react-day-picker wrapper with emerald theme |
| `frontend/src/components/ui/NoAplicaField.tsx` | Label + checkbox + textarea/input with disable toggle |
| `frontend/src/components/ui/WeightInput.tsx` | Number input + kg/lb unit toggle |
| `frontend/src/components/ui/HeightInput.tsx` | cm input or ft+in dual inputs with unit toggle |
| `frontend/src/constants/objectives.ts` | Shared OBJECTIVE_OPTIONS constant |

## Files to Modify

| File | Changes |
|------|---------|
| `frontend/src/pages/PublicIntake.tsx` | DatePicker replaces native date input; objectives → select; NoAplicaField on 5 clinical fields; refactor weight/height to shared components |
| `frontend/src/components/patients/PatientDrawer.tsx` | DatePicker replaces native date input; objectives → unified select; NoAplicaField on 4 fields; WeightInput/HeightInput in metrics section |
| `frontend/src/pages/PatientDetail.tsx` | DatePicker replaces native date input; objectives → unified select; NoAplicaField on 4 fields; WeightInput/HeightInput in metrics form; display values with unit conversion option |
| `frontend/src/types/index.ts` | Add types for new component props if needed |

## New Dependency

```json
"react-day-picker": "^9.x"
```

## Verification

1. **DatePicker**: Open PatientDrawer → click birth date → verify month/year dropdowns allow jumping to 1980 instantly → select date → verify formatted display
2. **Objectives**: Open PatientDrawer → verify 8 options in select → repeat in PatientDetail and PublicIntake
3. **No Aplica**: Open PublicIntake → check "No aplica" on Alergias → verify textarea disables → uncheck → verify re-enables → submit form → verify "No aplica" sent to backend
4. **Units**: Open PatientDrawer → toggle weight to lb → enter 154 → verify stored as ~69.85 kg → toggle height to ft/in → enter 5'9" → verify stored as ~175 cm
5. **Backward compatibility**: Existing patient data displays correctly with new components (all values stored in metric)
6. **Build**: `cd frontend && npm run build` passes with no TS errors
