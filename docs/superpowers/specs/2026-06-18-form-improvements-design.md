# Form Improvements — Design Spec

**Date:** 2026-06-18
**Status:** Approved
**Branch:** dev

## Overview

Five improvements to the doctor's patient form and validation messages:
1. Fix country/city selector not appearing (replace plain inputs with LocationSelector)
2. Remove forced decimal formatting from metric inputs (weight, height, water)
3. Convert free-text food preference fields to selectable pills
4. Translate all validation/diet-blocker messages to Spanish and make them doctor-friendly
5. Add save-time warning when fields required for diet creation are missing

---

## Fix 1: Country/City — Replace plain inputs with LocationSelector

### Current State
`PatientDetail.tsx` lines 990-1009: country and city are plain `<input type="text">` fields. The `LocationSelector` component (searchable dropdown with country→city cascade) exists but is only used in `PublicIntake.tsx`.

### Desired Behavior
Doctor sees the same searchable country/city dropdown that patients see in the public intake form.

### Implementation
In `PatientDetail.tsx`, in the "Datos Demográficos" editing form section:
- Replace the two plain inputs (country, city) with a `<LocationSelector>` component
- Import `LocationSelector` from `"../components/LocationSelector"`
- Add `country` and `city` state variables to track the selected values
- The LocationSelector handles its own internal search/dropdown state

### Files Changed
| File | Change |
|------|--------|
| `frontend/src/pages/PatientDetail.tsx` | Add LocationSelector import, add country/city state, replace inputs |

---

## Fix 2: Metrics — Remove forced decimal formatting

### Current State
- `WeightInput.tsx`: `step="0.1"` on input, `toFixed(2)` in `handleValueChange` (line 41), `toFixed(1)` in display (line 29)
- `HeightInput.tsx`: `step="0.1"` on cm input (line 74), `toFixed(1)` in `handleCmChange` (line 43)
- `PatientDetail.tsx`: `step="0.1"` on water_intake_liters (line 1227), `step="0.5"` on sleep_hours (line 1306)

### Desired Behavior
All metric inputs accept free-form numbers — doctor types exactly what they want. No automatic decimal formatting, no step restriction.

### Implementation

#### WeightInput.tsx
- Remove `step="0.1"` from input (line 52)
- Change `toFixed(2)` to direct string conversion in `handleValueChange` (line 41)
- Change `toFixed(1)` to direct conversion in lb display (line 29)
- Remove `min="0"` to allow free typing (browser still validates type="number")

#### HeightInput.tsx
- Remove `step="0.1"` from cm input (line 74)
- Change `toFixed(1)` to direct string conversion in `handleCmChange` (line 43)

#### PatientDetail.tsx
- Remove `step="0.1"` from water_intake_liters input
- Remove `step="0.5"` from sleep_hours input

### Files Changed
| File | Change |
|------|--------|
| `frontend/src/components/ui/WeightInput.tsx` | Remove step, remove toFixed |
| `frontend/src/components/ui/HeightInput.tsx` | Remove step, remove toFixed |
| `frontend/src/pages/PatientDetail.tsx` | Remove step from numeric inputs |

---

## Fix 3: Food Preferences — Convert to selectable pills

### Current State
- `food_preferences` (Alimentos que le gustan): `<textarea>` free text (line 1199)
- `disliked_foods` (Alimentos que NO le gustan): `<textarea>` free text (line 1212)

### Desired Behavior
Both fields use `PillSelect` with predefined food group options + an "Otro" option that reveals a text input for custom entries.

### Food groups for pills
```
Carnes rojas, Pollo, Pescado, Mariscos, Cerdo,
Verduras, Frutas, Arroz, Pasta, Pan, Legumbres,
Huevos, Lácteos, Frutos secos, Dulces
```

### Implementation

1. Define `FOOD_PREFERENCES_OPTIONS` constant array in PatientDetail.tsx
2. Add state variables: `foodPrefsPills`, `foodPrefsOther`, `dislikedPills`, `dislikedOther`
3. Initialize from existing profile data using `parseMultiValue`
4. Replace both `<textarea>` fields with `<PillSelect>` components
5. On save, use `buildMultiValue` to combine pills + other text back into comma-separated string
6. Keep backward compatibility: existing comma-separated data in DB still works

### Files Changed
| File | Change |
|------|--------|
| `frontend/src/pages/PatientDetail.tsx` | Add constant, state, replace textareas with PillSelect |

---

## Fix 4: Spanish & Doctor-Friendly Validation Messages

### Current State
7 messages in `diet_eligibility.py` are in English. Several error messages in `diet_service.py` and `diets.py` are in English. Some `input_builder.py` and `engine.py` messages are in Spanish but use technical jargon.

### Desired Behavior
All user-facing messages in Spanish, written for a doctor (not a programmer).

### Message translation table

| File | Line | Current (EN/Technical) | New (ES Doctor-Friendly) |
|------|------|------------------------|--------------------------|
| `diet_eligibility.py` | 16 | `Missing patient birth_date` | `Falta la fecha de nacimiento del paciente` |
| `diet_eligibility.py` | 18 | `Missing patient sex` | `Falta el sexo del paciente` |
| `diet_eligibility.py` | 20 | `Missing patient country or city` | `Falta el país o ciudad del paciente` |
| `diet_eligibility.py` | 22 | `Missing clinical profile` | `Falta completar el perfil clínico del paciente` |
| `diet_eligibility.py` | 25 | `Missing profile objective` | `Falta el objetivo del paciente en el perfil clínico` |
| `diet_eligibility.py` | 31 | `Missing latest weight (add a metric)` | `Falta registrar el peso del paciente en métricas` |
| `diet_eligibility.py` | 33 | `Missing latest height (add a metric)` | `Falta registrar la altura del paciente en métricas` |
| `diet_service.py` | 72 | `Patient not found` | `Paciente no encontrado` |
| `diet_service.py` | 226, 232 | `Patient data incomplete for diet generation` | `Faltan datos del paciente para crear la dieta` |
| `diet_service.py` | 255 | `Model error: {e}` | `Error al generar la dieta. Revise los datos e intente de nuevo.` |
| `diets.py` | 141, 153, 284 | `Diet not found` | `Dieta no encontrada` |
| `diet_service.py` | 302 | `La dieta no está pendiente de aprobación` | (OK, already Spanish) |
| `input_builder.py` | 46 | `Falta métrica numérica.` | `Falta un valor numérico requerido para el cálculo.` |
| `input_builder.py` | 57 | `Sexo no reconocido para el cálculo nutricional (use male/female o equivalente).` | `El sexo ingresado no es válido. Use Masculino o Femenino.` |
| `engine.py` | 124 | `Edad fuera del rango soportado (14–100 años) para este motor.` | `La edad debe estar entre 14 y 100 años.` |
| `engine.py` | 240-242 | `Hay condiciones de salud no clasificadas en las reglas del sistema...` | `El paciente tiene condiciones de salud que requieren revisión manual antes de generar la dieta.` |

### Files Changed
| File | Change |
|------|--------|
| `backend/app/logic/diet_eligibility.py` | Translate 7 messages to Spanish |
| `backend/app/services/diet_service.py` | Translate 3 messages to Spanish |
| `backend/app/api/diets.py` | Translate "Diet not found" (3 occurrences) |
| `backend/app/nutrition/input_builder.py` | Simplify 2 technical messages |
| `backend/app/nutrition/engine.py` | Simplify 2 technical messages |

---

## Fix 5: Save-Time Warning for Missing Diet Fields

### Current State
When doctor saves patient data, there is no validation for diet readiness. The doctor only discovers missing fields when they try to generate a diet and get a blocking error.

### Desired Behavior
When doctor clicks "Guardar" on patient data or profile, if any of the 10 diet-required fields are missing, show a **warning toast** listing what's missing. The save still succeeds — it's just a warning, not a blocker.

### Implementation

#### Frontend: `PatientDetail.tsx`
After successful save of "Datos Demográficos" or "Perfil Clínico":
1. Check saved data against the 10 required fields for diet generation
2. If any are missing, call `addToast()` with an info message listing them
3. Format example: `"Para crear una dieta, falta: fecha de nacimiento, peso, altura."`

#### Required fields to check (subset verifiable from frontend state):
| # | Field | Check |
|---|-------|-------|
| 1 | Fecha nacimiento | `!patient.birth_date` |
| 2 | Sexo | `!patient.sex` |
| 3 | País | `!patient.country` |
| 4 | Ciudad | `!patient.city` |
| 5 | Objetivo | `!profile.objective` |
| 6 | Alergias alimentarias | `!profile.food_allergies` |
| 7 | Alimentos a evitar | `!profile.foods_avoided` |
| 8 | Peso | No latest metric with weight_kg |
| 9 | Altura | No latest metric with height_cm |
| 10 | Perfil clínico existe | `!profile` or `!profile.completed_at` |

Note: the frontend check is best-effort (warns about obvious gaps). The backend remains the authoritative blocker at diet generation time.

### Files Changed
| File | Change |
|------|--------|
| `frontend/src/pages/PatientDetail.tsx` | Add diet-readiness check after save, show info toast |

---

## Edge Cases & Error Handling

- **LocationSelector:** If country has no cities in data, city field shows free-text input (existing behavior in component)
- **Metrics:** Empty input → treated as null (existing behavior). Non-numeric input → rejected by browser (type="number")
- **Food pills:** Existing patients with free-text food preferences → `parseMultiValue` splits on commas, known values become pills, unknown values go to "Otro" text

---

## Testing Checklist

- [ ] Country dropdown appears when clicking country field in doctor form
- [ ] City dropdown filters by selected country
- [ ] Weight accepts integers and decimals without forced formatting
- [ ] Height accepts integers and decimals without forced formatting
- [ ] Water intake accepts free-form numbers
- [ ] Food preferences show as clickable pills
- [ ] "Otro" option reveals text input for custom foods
- [ ] Save preserves all values correctly
- [ ] Existing patient data displays correctly (backward compatible)
