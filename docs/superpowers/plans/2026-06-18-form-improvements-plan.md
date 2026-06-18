# Form Improvements — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Five improvements to the doctor's patient form: LocationSelector, decimal-free metrics, food pills, Spanish validation messages, and save-time diet-readiness warning.

**Architecture:** Frontend changes in PatientDetail.tsx (LocationSelector, food pills, diet-readiness warning), WeightInput.tsx, HeightInput.tsx (decimal removal). Backend string changes in 5 files (Spanish translations). No new endpoints or DB changes.

**Tech Stack:** React/TypeScript, Tailwind CSS, Python/FastAPI

---

## File Map

| File | Action | Responsibility |
|------|--------|---------------|
| `frontend/src/pages/PatientDetail.tsx` | Modify | LocationSelector, food pills, decimal removal, diet-readiness warning |
| `frontend/src/components/ui/WeightInput.tsx` | Modify | Remove step/toFixed |
| `frontend/src/components/ui/HeightInput.tsx` | Modify | Remove step/toFixed |
| `backend/app/logic/diet_eligibility.py` | Modify | Translate 7 messages to Spanish |
| `backend/app/services/diet_service.py` | Modify | Translate 3 messages to Spanish |
| `backend/app/api/diets.py` | Modify | Translate "Diet not found" |
| `backend/app/nutrition/input_builder.py` | Modify | Simplify 2 technical messages |
| `backend/app/nutrition/engine.py` | Modify | Simplify 2 technical messages |

---

### Task 1: Replace plain country/city inputs with LocationSelector in PatientDetail

**Files:**
- Modify: `frontend/src/pages/PatientDetail.tsx`

- [ ] **Step 1: Add LocationSelector import**

At the top of PatientDetail.tsx (after the existing imports, around line 6), add:

```typescript
import LocationSelector from "../components/LocationSelector"
```

- [ ] **Step 2: Add country and city state variables**

After the existing state declarations (after line 352, near `const [editingProfile, setEditingProfile] = useState(false)`), add:

```typescript
  const [editCountry, setEditCountry] = useState(patient?.country ?? "")
  const [editCity, setEditCity] = useState(patient?.city ?? "")
```

- [ ] **Step 3: Reset country/city state when entering edit mode**

In the "Editar" button onClick handler (around line 747), add after `setEditBirthDate(...)` and `setEditMedications(...)`:

```typescript
                setEditCountry(patient.country ?? "")
                setEditCity(patient.city ?? "")
```

- [ ] **Step 4: Replace the country and city plain inputs with LocationSelector**

Find the country input (lines 989-998) and city input (lines 1000-1009) in the editing form. Replace both with:

```tsx
            <LocationSelector
              country={editCountry}
              city={editCity}
              onCountryChange={(c) => { setEditCountry(c); setEditCity("") }}
              onCityChange={setEditCity}
            />
```

- [ ] **Step 5: Update onSaveData to use editCountry and editCity**

In the `onSaveData` function (around line 468), replace the country and city lines:

Replace:
```typescript
        country: (fd.get("country") as string) || null,
        city: (fd.get("city") as string) || null,
```

With:
```typescript
        country: editCountry || null,
        city: editCity || null,
```

- [ ] **Step 6: Commit**

```bash
git add frontend/src/pages/PatientDetail.tsx
git commit -m "feat: replace plain country/city inputs with LocationSelector in doctor form

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

### Task 2: Remove forced decimal formatting from WeightInput and HeightInput

**Files:**
- Modify: `frontend/src/components/ui/WeightInput.tsx`
- Modify: `frontend/src/components/ui/HeightInput.tsx`

- [ ] **Step 1: Fix WeightInput.tsx — remove step and toFixed**

Read the file and apply 3 changes:

**Change A:** Line 52 — Remove `step="0.1"`:
```tsx
// Before:
        step="0.1"
        min="0"
// After:
        min="0"
```

**Change B:** Line 41 — Replace `toFixed(2)`:
```tsx
// Before:
    onChangeKg(kgValue.toFixed(2));
// After:
    onChangeKg(String(kgValue));
```

**Change C:** Line 29 — Replace `toFixed(1)`:
```tsx
// Before:
    return (kg / WEIGHT_LB_TO_KG).toFixed(1);
// After:
    return String(kg / WEIGHT_LB_TO_KG);
```

- [ ] **Step 2: Fix HeightInput.tsx — remove step and toFixed**

**Change A:** Line 74 — Remove `step="0.1"`:
```tsx
// Before:
        step="0.1"
        min="0"
// After:
        min="0"
```

**Change B:** Line 43 — Replace `toFixed(1)`:
```tsx
// Before:
    onChangeCm(num.toFixed(1));
// After:
    onChangeCm(String(num));
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/ui/WeightInput.tsx frontend/src/components/ui/HeightInput.tsx
git commit -m "fix: remove forced decimal formatting from weight and height inputs

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

### Task 3: Remove decimal step from PatientDetail numeric fields + convert food preferences to pills

**Files:**
- Modify: `frontend/src/pages/PatientDetail.tsx`

- [ ] **Step 1: Remove step from numeric inputs**

**Change A:** Find water_intake_liters input (around line 1226). Remove `step="0.1"`:
```tsx
// Before:
                    type="number"
                    step="0.1"
                    min="0"
// After:
                    type="number"
                    min="0"
```

**Change B:** Find sleep_hours input (around line 1305). Remove `step="0.5"`:
```tsx
// Before:
                    type="number"
                    step="0.5"
                    min="3"
// After:
                    type="number"
                    min="3"
```

- [ ] **Step 2: Add FOOD_PREFERENCES_OPTIONS constant**

After the existing `FOODS_AVOIDED_OPTIONS` constant (around line 67), add:

```typescript
const FOOD_PREFERENCES_OPTIONS = [
  "Carnes rojas", "Pollo", "Pescado", "Mariscos", "Cerdo",
  "Verduras", "Frutas", "Arroz", "Pasta", "Pan", "Legumbres",
  "Huevos", "Lácteos", "Frutos secos", "Dulces",
]
```

Use the same list for both `food_preferences` and `disliked_foods` pills.

- [ ] **Step 3: Add state for food preferences and disliked foods pills**

After the existing pill state declarations (around line 385), add:

```typescript
  const [foodPrefsPills, setFoodPrefsPills] = useState<string[]>([])
  const [foodPrefsOther, setFoodPrefsOther] = useState("")
  const [dislikedPills, setDislikedPills] = useState<string[]>([])
  const [dislikedOther, setDislikedOther] = useState("")
```

- [ ] **Step 4: Initialize food pill state from profile data**

In the useEffect that initializes pills from profile (around line 388), add after the foodsAvoided initialization:

```typescript
    const [fpp, fpo] = parseMultiValue(profile.food_preferences, FOOD_PREFERENCES_OPTIONS)
    setFoodPrefsPills(fpp)
    setFoodPrefsOther(fpo)
    const [dp, do_] = parseMultiValue(profile.disliked_foods, FOOD_PREFERENCES_OPTIONS)
    setDislikedPills(dp)
    setDislikedOther(do_)
```

- [ ] **Step 5: Replace food_preferences textarea with PillSelect**

Find the textarea for `food_preferences` (around lines 1194-1203). Replace with:

```tsx
                <div>
                  <label className="block text-xs font-medium text-slate-500 mb-1">
                    Alimentos que le gustan
                  </label>
                  <PillSelect
                    options={FOOD_PREFERENCES_OPTIONS}
                    selected={foodPrefsPills}
                    otherText={foodPrefsOther}
                    onChange={setFoodPrefsPills}
                    onOtherChange={setFoodPrefsOther}
                  />
                </div>
```

- [ ] **Step 6: Replace disliked_foods textarea with PillSelect**

Find the textarea for `disliked_foods` (around lines 1207-1217). Replace with:

```tsx
                <div>
                  <label className="block text-xs font-medium text-slate-500 mb-1">
                    Alimentos que NO le gustan
                  </label>
                  <PillSelect
                    options={FOOD_PREFERENCES_OPTIONS}
                    selected={dislikedPills}
                    otherText={dislikedOther}
                    onChange={setDislikedPills}
                    onOtherChange={setDislikedOther}
                  />
                </div>
```

- [ ] **Step 7: Update onSaveProfile to use buildMultiValue for food fields**

In `onSaveProfile` (around line 504), replace:
```typescript
      food_preferences: (fd.get("food_preferences") as string) || null,
      disliked_foods: (fd.get("disliked_foods") as string) || null,
```

With:
```typescript
      food_preferences: buildMultiValue(foodPrefsPills, foodPrefsOther),
      disliked_foods: buildMultiValue(dislikedPills, dislikedOther),
```

- [ ] **Step 8: Commit**

```bash
git add frontend/src/pages/PatientDetail.tsx
git commit -m "feat: remove decimal steps, add food preference pills to doctor form

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

### Task 4: Translate all validation messages to Spanish (doctor-friendly)

**Files:**
- Modify: `backend/app/logic/diet_eligibility.py`
- Modify: `backend/app/services/diet_service.py`
- Modify: `backend/app/api/diets.py`
- Modify: `backend/app/nutrition/input_builder.py`
- Modify: `backend/app/nutrition/engine.py`

- [ ] **Step 1: Translate diet_eligibility.py (7 messages)**

In `backend/app/logic/diet_eligibility.py`, replace lines 16-33:

```python
def diet_generation_blockers(
    patient: Patient,
    profile: Optional[PatientProfile],
    latest: Optional[PatientMetrics],
) -> List[str]:
    reasons: List[str] = []
    if patient.deleted_at:
        reasons.append("El paciente ha sido eliminado")
    if not patient.birth_date:
        reasons.append("Falta la fecha de nacimiento del paciente")
    if not patient.sex:
        reasons.append("Falta el sexo del paciente")
    if not patient.country or not patient.city:
        reasons.append("Falta el país o ciudad del paciente")
    if not profile:
        reasons.append("Falta completar el perfil clínico del paciente")
    else:
        if not profile.objective:
            reasons.append("Falta el objetivo del paciente en el perfil clínico")
        if not norm(profile.food_allergies):
            reasons.append("Faltan alergias alimentarias (escribe 'ninguna' si no aplica)")
        if not norm(profile.foods_avoided):
            reasons.append("Faltan alimentos a evitar (escribe 'ninguno' si no aplica)")
    if not latest or latest.weight_kg is None:
        reasons.append("Falta registrar el peso del paciente en métricas")
    if not latest or latest.height_cm is None:
        reasons.append("Falta registrar la altura del paciente en métricas")
    return reasons
```

- [ ] **Step 2: Translate diet_service.py (3 messages)**

In `backend/app/services/diet_service.py`:

**Line 72:** Replace `"Patient not found"` with `"Paciente no encontrado"`

**Lines 226-227:** Replace `"incomplete_profile", "Patient data incomplete for diet generation"` with `"incomplete_profile", "Faltan datos del paciente para crear la dieta"`

**Line 232-233:** Replace `"incomplete_profile", "Patient data incomplete for diet generation"` with `"incomplete_profile", "Faltan datos del paciente para crear la dieta"`

**Lines 254-256:** Replace:
```python
        raise DietGenerationError(
            "openai_error",
            f"Model error: {e}",
        ) from e
```
With:
```python
        raise DietGenerationError(
            "openai_error",
            "Error al generar la dieta. Revise los datos e intente de nuevo.",
        ) from e
```

- [ ] **Step 3: Translate diets.py (3 occurrences)**

In `backend/app/api/diets.py`, find all 3 occurrences of `detail="Diet not found"` (lines 141, 153, 284) and replace with `detail="Dieta no encontrada"`.

Also find the occurrence at line 358 and the email endpoint at line 359. Replace those too if they say "Diet not found".

- [ ] **Step 4: Simplify input_builder.py (2 messages)**

In `backend/app/nutrition/input_builder.py`:

**Line 46:** Replace `"Falta métrica numérica."` with `"Falta un valor numérico requerido para el cálculo."`

**Line 57:** Replace `"Sexo no reconocido para el cálculo nutricional (use male/female o equivalente)."` with `"El sexo ingresado no es válido. Use Masculino o Femenino."`

- [ ] **Step 5: Simplify engine.py (2 messages)**

In `backend/app/nutrition/engine.py`:

**Line 124:** Replace `"Edad fuera del rango soportado (14–100 años) para este motor."` with `"La edad debe estar entre 14 y 100 años."`

**Lines 240-242:** Replace:
```python
                message_es="Hay condiciones de salud no clasificadas en las reglas del sistema; "
                "revise manualmente antes de generar.",
```
With:
```python
                message_es="El paciente tiene condiciones de salud que requieren revisión manual antes de generar la dieta.",
```

- [ ] **Step 6: Commit**

```bash
git add backend/app/logic/diet_eligibility.py backend/app/services/diet_service.py backend/app/api/diets.py backend/app/nutrition/input_builder.py backend/app/nutrition/engine.py
git commit -m "fix: translate all validation messages to Spanish with doctor-friendly language

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

### Task 5: Add save-time diet-readiness warning in PatientDetail

**Files:**
- Modify: `frontend/src/pages/PatientDetail.tsx`

- [ ] **Step 1: Add helper function that checks diet-readiness**

After the existing helper functions (around line 150, after `formatDate`), add:

```typescript
function checkDietReadiness(
  patientData: Partial<Patient>,
  profileData: Partial<PatientProfile> | null,
  latestMetric: PatientMetric | null | undefined,
): string[] {
  const missing: string[] = []
  if (!patientData.birth_date) missing.push("fecha de nacimiento")
  if (!patientData.sex) missing.push("sexo")
  if (!patientData.country || !patientData.city) missing.push("país o ciudad")
  if (!profileData) {
    missing.push("perfil clínico")
  } else {
    if (!profileData.objective) missing.push("objetivo")
    if (!profileData.food_allergies) missing.push("alergias alimentarias")
    if (!profileData.foods_avoided) missing.push("alimentos a evitar")
  }
  if (!latestMetric || latestMetric.weight_kg == null) missing.push("peso")
  if (!latestMetric || latestMetric.height_cm == null) missing.push("altura")
  return missing
}
```

- [ ] **Step 2: Add warning toast after saving patient data**

In the `onSaveData` function, after `setPatient(p)` and before `setEditingData(false)` (around line 481), add:

```typescript
      const missing = checkDietReadiness(p, profile, summary?.latest_metrics)
      if (missing.length > 0) {
        addToast(
          `Para crear una dieta, aún falta: ${missing.join(", ")}.`,
          "info",
        )
      }
```

- [ ] **Step 3: Add warning toast after saving profile**

In the `onSaveProfile` function's confirm callback (around line 549-553), after `setProfile(pr)` and before `setEditingProfile(false)`, add:

```typescript
          const missing = checkDietReadiness(patient, pr, summary?.latest_metrics)
          if (missing.length > 0) {
            addToast(
              `Para crear una dieta, aún falta: ${missing.join(", ")}.`,
              "info",
            )
          }
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/pages/PatientDetail.tsx
git commit -m "feat: add save-time warning when diet-required fields are missing

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Verification Checklist

- [ ] Country dropdown with search appears when editing patient demographics
- [ ] City dropdown filters by selected country
- [ ] Weight: type "65" → stays "65" (not "65.00"), type "65.5" → stays "65.5"
- [ ] Height: type "170" → stays "170" (not "170.0")
- [ ] Food preferences: clickable pills + "Otro" text input
- [ ] Disliked foods: clickable pills + "Otro" text input
- [ ] Save patient data → warning toast if birth_date missing
- [ ] Save profile → warning toast if objective/food_allergies missing
- [ ] Try generating diet with incomplete patient → Spanish error message
- [ ] Try generating diet with missing metrics → "Falta registrar el peso..."
- [ ] All error messages appear in Spanish
