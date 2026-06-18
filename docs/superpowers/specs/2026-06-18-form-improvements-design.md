# Form Improvements — Design Spec

**Date:** 2026-06-18
**Status:** Approved
**Branch:** dev

## Overview

Three improvements to the doctor's patient form (PatientDetail):
1. Fix country/city selector not appearing (replace plain inputs with LocationSelector)
2. Remove forced decimal formatting from metric inputs (weight, height, water)
3. Convert free-text food preference fields to selectable pills

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
