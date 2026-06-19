# Form Refactor — Intake & Profile Improvements

## Context

Analysis of the patient intake form and doctor profile found 9 issues: duplicated fields, redundant options, unmapped values, and confusing labels. This spec covers all fixes using backward-compatible approaches.

## Changes (by priority)

### 🔴 1. Consolidate `disliked_foods` + `foods_avoided`

**Strategy:** Single UI field → populates both DB columns for backward compatibility.

- **Intake form:** Change field from `disliked_foods` to `foods_avoided`. Same textarea UX.
- **Doctor form:** Remove `disliked_foods` section. Keep `foods_avoided` PillSelect. On save, write same value to both columns.
- **PatientDrawer:** Single field.
- **Profile completeness:** Already checks `foods_avoided`. Now intake fills it → patient becomes diet-ready.
- **Engine:** Merge both fields with dedup before passing to LLM.
- **Intake API:** Save to `foods_avoided` instead of `disliked_foods`.

### 🟡 2. Remove duplicate `fat_loss` objective

Remove `{ value: "fat_loss", label: "Pérdida de grasa" }` from OBJECTIVE_OPTIONS. Both `lose_weight` and `fat_loss` map to `FAT_LOSS` internally.

### 🟡 3. De-duplicate allergy vs avoided food pills

Remove from `FOODS_AVOIDED_OPTIONS`: "Mariscos", "Gluten", "Lacteos". Keep in `ALLERGY_OPTIONS`.

### 🟡 4. Align `dietary_style` with backend enum

Replace current pills with backend-supported values: Equilibrada, Baja en carbohidratos, Alta en carbohidratos, Alta en proteína, Mediterránea.

### 🟡 5. Map `health_improvement` and `sports_performance` to real goals

In `_normalize_goal()`: `health_improvement` → `FAT_LOSS`, `sports_performance` → `MUSCLE_GAIN`.

### 🟡 6. Simplify update flow

In UPDATE mode, hide first_name and last_name fields. Only show weight, country, city.

### 🟢 7. Sex dropdown on intake

Replace free-text `<input>` with `<select>`: Femenino / Masculino / Otro.

### 🟢 8. Add `food_preferences` to doctor form

New PillSelect "Alimentos que SÍ le gustan" saving to existing `food_preferences` column.

### 🟢 9. Rename misleading section header

"Objetivo y preferencias" → "Objetivo y alimentos a evitar".

## Files affected

| File | Issues |
|------|--------|
| `frontend/src/pages/PublicIntake.tsx` | #1, #6, #7, #9 |
| `frontend/src/pages/PatientDetail.tsx` | #1, #3, #4, #8 |
| `frontend/src/components/patients/PatientDrawer.tsx` | #1 |
| `frontend/src/constants/objectives.ts` | #2 |
| `backend/app/nutrition/input_builder.py` | #1, #5 |
| `backend/app/api/intake_links.py` | #1 |

## Non-breaking guarantee

- No DB migrations (both columns preserved)
- No API contract changes
- Engine behavior: previously mapped values produce same results
- All existing patient data remains valid
