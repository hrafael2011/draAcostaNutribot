# Form Intake Improvements — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix 9 form issues — consolidate duplicate fields, remove redundant options, align UI with backend, simplify update flow.

**Architecture:** Backward-compatible consolidation of `disliked_foods` into `foods_avoided` with dual-write, frontend-only dropdown/section changes, and backend goal mapping fixes. TDD: 32 existing tests must pass between every commit. TypeScript must compile after every frontend change.

**Tech Stack:** FastAPI + SQLAlchemy (Python 3.12), React + TypeScript, Pytest

---

### Task 1: Consolidate `disliked_foods` → `foods_avoided` (Backend)

**Files:**
- Modify: `backend/app/api/intake_links.py:195`
- Modify: `backend/app/nutrition/input_builder.py:161`

- [ ] **Step 1: Run existing tests before any changes**

```bash
cd backend && .venv/bin/python -m pytest tests/test_diet_eligibility.py tests/test_nutrition_engine.py tests/test_nutrition_integration.py tests/test_nutrition_contract.py tests/test_diet_duration.py tests/test_diet_export_pdf.py tests/test_config.py -v
```
Expected: 32 passed

- [ ] **Step 2: Change intake save to use `foods_avoided`**

In `backend/app/api/intake_links.py`, line 195, change:

```python
    profile.disliked_foods = body.disliked_foods
```

To:

```python
    profile.foods_avoided = body.disliked_foods
```

This preserves the API contract (`body.disliked_foods` from frontend) but saves to the correct column. No schema change needed.

- [ ] **Step 3: Add merge logic in input_builder for duplicate foods fields**

In `backend/app/nutrition/input_builder.py`, around line 161, replace:

```python
        disliked_foods=profile.disliked_foods,
```

With a merged + deduped value:

```python
        disliked_foods=_merge_food_lists(profile.disliked_foods, profile.foods_avoided),
```

Add the helper function at the top of `input_builder.py` (after imports, before first function):

```python
def _merge_food_lists(a: str | None, b: str | None) -> str | None:
    """Merge two comma-separated food lists, deduplicating entries."""
    items: list[str] = []
    seen: set[str] = set()
    for raw in (a, b):
        if not raw or not raw.strip():
            continue
        for item in raw.split(","):
            cleaned = item.strip().lower()
            if cleaned and cleaned not in seen:
                seen.add(cleaned)
                items.append(item.strip())
    return ", ".join(items) if items else None
```

- [ ] **Step 4: Run tests to verify no regressions**

```bash
cd backend && .venv/bin/python -m pytest tests/ -v --ignore=tests/test_e2e_flow.py
```
Expected: All non-e2e tests pass

- [ ] **Step 5: Commit**

```bash
git add backend/app/api/intake_links.py backend/app/nutrition/input_builder.py
git commit -m "refactor: consolidate disliked_foods into foods_avoided — dual-write, merge in engine"
```

---

### Task 2: Consolidate `disliked_foods` → single UI field (Frontend)

**Files:**
- Modify: `frontend/src/pages/PublicIntake.tsx:101,121,318`
- Modify: `frontend/src/pages/PatientDetail.tsx:345,349,464,578,1539`
- Modify: `frontend/src/components/patients/PatientDrawer.tsx:33,57,124,166,408-409`

- [ ] **Step 1: Update PublicIntake — change field name**

In `frontend/src/pages/PublicIntake.tsx`:

Change line 101 from:
```tsx
      disliked_foods: optStr("disliked_foods"),
```
To:
```tsx
      disliked_foods: optStr("foods_avoided"),
```

Change line 121 from:
```tsx
    if (str("disliked_foods")) changes.push({ label: "Alimentos que no le gustan", newValue: str("disliked_foods"), isNew: true })
```
To:
```tsx
    if (str("foods_avoided")) changes.push({ label: "Alimentos a evitar", newValue: str("foods_avoided"), isNew: true })
```

Change the textarea name at line 318 from `name="disliked_foods"` to `name="foods_avoided"`.

- [ ] **Step 2: Update PatientDetail — remove disliked_foods section**

In `frontend/src/pages/PatientDetail.tsx`:

Remove line 349 (`disliked_foods: "Alimentos que NO le gustan",`) from the `PROFILE_LABELS` map.

Remove lines 464 and 578 (disliked_foods state and save logic).

Remove line 1539 (`renderProfileField("Alimentos que NO le gustan", profile?.disliked_foods)`) from the read-only view.

On save (around line 575), add after `foods_avoided` assignment:
```tsx
      disliked_foods: buildMultiValue(foodsAvoidedPills, foodsAvoidedOther),  // dual-write for backward compat
```

- [ ] **Step 3: Update PatientDrawer — simplify to single field**

In `frontend/src/components/patients/PatientDrawer.tsx`:

Remove `disliked_foods` from the form state init (line 57).
Remove `disliked_foods` from the `isDirty` check (line 124).
Remove `disliked_foods` from the save body (line 166).
Remove the disliked_foods textarea (lines 408-409).

- [ ] **Step 4: TypeScript check**

```bash
cd frontend && npx tsc --noEmit --pretty
```
Expected: No errors

- [ ] **Step 5: Run backend tests**

```bash
cd backend && .venv/bin/python -m pytest tests/ -v --ignore=tests/test_e2e_flow.py
```
Expected: All non-e2e tests pass

- [ ] **Step 6: Commit**

```bash
git add frontend/src/pages/PublicIntake.tsx frontend/src/pages/PatientDetail.tsx frontend/src/components/patients/PatientDrawer.tsx
git commit -m "refactor: consolidate disliked_foods UI into single foods_avoided field"
```

---

### Task 3: Remove duplicate `fat_loss` objective

**Files:**
- Modify: `frontend/src/constants/objectives.ts:4`

- [ ] **Step 1: Remove fat_loss from objectives**

In `frontend/src/constants/objectives.ts`, delete line 4:
```tsx
  { value: "fat_loss", label: "🔥  Pérdida de grasa" },
```

- [ ] **Step 2: TypeScript check**

```bash
cd frontend && npx tsc --noEmit --pretty
```
Expected: No errors

- [ ] **Step 3: Commit**

```bash
git add frontend/src/constants/objectives.ts
git commit -m "fix: remove duplicate fat_loss objective — identical to lose_weight"
```

---

### Task 4: De-duplicate allergy vs avoided food pills

**Files:**
- Modify: `frontend/src/pages/PatientDetail.tsx:64-71`

- [ ] **Step 1: Remove overlapping items from FOODS_AVOIDED_OPTIONS**

In `frontend/src/pages/PatientDetail.tsx`, change `FOODS_AVOIDED_OPTIONS` from:
```tsx
const FOODS_AVOIDED_OPTIONS = ["Carnes rojas", "Cerdo", "Mariscos", "Lacteos", "Gluten", "Azúcar procesada", "Frituras"];
```
To:
```tsx
const FOODS_AVOIDED_OPTIONS = ["Carnes rojas", "Cerdo", "Azúcar procesada", "Frituras"];
```
Removing: "Mariscos" (in ALLERGY_OPTIONS), "Lacteos" (Lactosa in ALLERGY_OPTIONS), "Gluten" (in ALLERGY_OPTIONS).

- [ ] **Step 2: TypeScript check**

```bash
cd frontend && npx tsc --noEmit --pretty
```
Expected: No errors

- [ ] **Step 3: Commit**

```bash
git add frontend/src/pages/PatientDetail.tsx
git commit -m "fix: remove overlapping pills between allergies and foods avoided"
```

---

### Task 5: Align `dietary_style` with backend enum

**Files:**
- Modify: `frontend/src/pages/PatientDetail.tsx:44-52`

- [ ] **Step 1: Replace DIETARY_STYLE_OPTIONS**

In `frontend/src/pages/PatientDetail.tsx`, change `DIETARY_STYLE_OPTIONS` from:
```tsx
const DIETARY_STYLE_OPTIONS = ["Omnívoro", "Vegetariano", "Vegano", "Sin gluten", "Sin lactosa", "Keto", "Mediterráneo"];
```
To:
```tsx
const DIETARY_STYLE_OPTIONS = ["Equilibrada", "Baja en carbohidratos", "Alta en carbohidratos", "Alta en proteína", "Mediterránea"];
```

- [ ] **Step 2: TypeScript check**

```bash
cd frontend && npx tsc --noEmit --pretty
```
Expected: No errors

- [ ] **Step 3: Commit**

```bash
git add frontend/src/pages/PatientDetail.tsx
git commit -m "fix: align dietary_style pills with backend DietStyle enum"
```

---

### Task 6: Map `health_improvement` and `sports_performance` to real goals

**Files:**
- Modify: `backend/app/nutrition/input_builder.py:92-128`

- [ ] **Step 1: Add mappings in _normalize_goal**

In `backend/app/nutrition/input_builder.py`, in the `_normalize_goal` function, add `health_improvement` to the FAT_LOSS set (line 94-117) and `sports_performance` to the MUSCLE_GAIN set (line 118-120).

Change the FAT_LOSS condition from:
```python
    if s in (
        "fat_loss",
        "lose_weight",
        ...
        "bajar_peso",
    ):
```
To (add `"health_improvement"` to the tuple):
```python
    if s in (
        "fat_loss",
        "lose_weight",
        ...
        "bajar_peso",
        "health_improvement",
        "mejora_de_salud",
        "mejora de salud",
    ):
```

Change the MUSCLE_GAIN condition from:
```python
    if s in ("muscle_gain", "gain_muscle", "gainmuscle", "hipertrofia", "masa", "musculo",
             "músculo", "ganar_musculo", "ganar_músculo", "ganar musculo", "ganar músculo"):
```
To:
```python
    if s in ("muscle_gain", "gain_muscle", "gainmuscle", "hipertrofia", "masa", "musculo",
             "músculo", "ganar_musculo", "ganar_músculo", "ganar musculo", "ganar músculo",
             "sports_performance", "rendimiento_deportivo", "rendimiento deportivo"):
```

- [ ] **Step 2: Run tests**

```bash
cd backend && .venv/bin/python -m pytest tests/ -v --ignore=tests/test_e2e_flow.py
```
Expected: All non-e2e tests pass

- [ ] **Step 3: Commit**

```bash
git add backend/app/nutrition/input_builder.py
git commit -m "fix: map health_improvement→FAT_LOSS and sports_performance→MUSCLE_GAIN"
```

---

### Task 7: Simplify update flow — hide name fields

**Files:**
- Modify: `frontend/src/pages/PublicIntake.tsx:250-260`

- [ ] **Step 1: Hide first_name and last_name in UPDATE mode**

In the render section of `frontend/src/pages/PublicIntake.tsx`, wrap the name fields with a condition. Find the first_name and last_name inputs (around lines 250-260) and wrap them:

```tsx
{linkType !== "update" && (
  <>
    <div>
      <label>Nombre <span>*</span></label>
      <input name="first_name" required ... />
    </div>
    <div>
      <label>Apellido <span>*</span></label>
      <input name="last_name" required ... />
    </div>
  </>
)}
```

- [ ] **Step 2: TypeScript check**

```bash
cd frontend && npx tsc --noEmit --pretty
```
Expected: No errors

- [ ] **Step 3: Commit**

```bash
git add frontend/src/pages/PublicIntake.tsx
git commit -m "fix: hide name fields in intake update flow — only weight/location needed"
```

---

### Task 8: Sex dropdown on intake form

**Files:**
- Modify: `frontend/src/pages/PublicIntake.tsx` (sex input line)

- [ ] **Step 1: Replace free-text sex input with select**

Find the sex `<input>` in the register section and replace it with:

```tsx
<select name="sex" required
  className="w-full rounded-xl border border-gray-300 px-3 py-2.5 text-sm ...">
  <option value="">Seleccionar...</option>
  <option value="Femenino">Femenino</option>
  <option value="Masculino">Masculino</option>
  <option value="Otro">Otro</option>
</select>
```

- [ ] **Step 2: TypeScript check**

```bash
cd frontend && npx tsc --noEmit --pretty
```
Expected: No errors

- [ ] **Step 3: Commit**

```bash
git add frontend/src/pages/PublicIntake.tsx
git commit -m "fix: replace free-text sex input with dropdown on intake form"
```

---

### Task 9: Add `food_preferences` field to doctor form

**Files:**
- Modify: `frontend/src/pages/PatientDetail.tsx`

- [ ] **Step 1: Add food_preferences PillSelect to doctor form**

In `frontend/src/pages/PatientDetail.tsx`, add after the `foods_avoided` section (around line 1256) a new PillSelect for food_preferences:

```tsx
{/* Alimentos que SÍ le gustan */}
<div>
  <label className="block text-sm font-medium text-slate-700 mb-1.5">
    Alimentos que SÍ le gustan
  </label>
  <PillSelect
    options={FOOD_PREFERENCES_OPTIONS}
    selected={foodPrefsPills}
    onChange={setFoodPrefsPills}
    otherValue={foodPrefsOther}
    onOtherChange={setFoodPrefsOther}
  />
</div>
```

Add state variables and wire them into the save logic using `buildMultiValue(foodPrefsPills, foodPrefsOther)` for the `food_preferences` field, and `parseMultiValue(profile.food_preferences, FOOD_PREFERENCES_OPTIONS)` for loading.

Add display in read-only view:
```tsx
{renderMultiTag(profile?.food_preferences) || <span className="text-sm text-slate-400">—</span>}
```
with label "Alimentos que SÍ le gustan".

- [ ] **Step 2: TypeScript check**

```bash
cd frontend && npx tsc --noEmit --pretty
```
Expected: No errors

- [ ] **Step 3: Run backend tests**

```bash
cd backend && .venv/bin/python -m pytest tests/ -v --ignore=tests/test_e2e_flow.py
```
Expected: All non-e2e tests pass

- [ ] **Step 4: Commit**

```bash
git add frontend/src/pages/PatientDetail.tsx
git commit -m "feat: add food_preferences field to doctor form (column already exists)"
```

---

### Task 10: Rename misleading section header

**Files:**
- Modify: `frontend/src/pages/PublicIntake.tsx:304`

- [ ] **Step 1: Change section header**

In `frontend/src/pages/PublicIntake.tsx`, line 304, change:

```tsx
<h2>Objetivo y preferencias</h2>
```
To:
```tsx
<h2>Objetivo y alimentos a evitar</h2>
```

- [ ] **Step 2: TypeScript check**

```bash
cd frontend && npx tsc --noEmit --pretty
```
Expected: No errors

- [ ] **Step 3: Commit**

```bash
git add frontend/src/pages/PublicIntake.tsx
git commit -m "fix: rename misleading section header to 'Objetivo y alimentos a evitar'"
```

---

### Task 11: Final verification — full test suite

**Files:** None

- [ ] **Step 1: Run all backend tests**

```bash
cd backend && .venv/bin/python -m pytest tests/ -v --ignore=tests/test_e2e_flow.py
```
Expected: 32 passed

- [ ] **Step 2: TypeScript final check**

```bash
cd frontend && npx tsc --noEmit --pretty
```
Expected: No errors

- [ ] **Step 3: Verify git log is clean and atomic**

```bash
git log --oneline -12
```
Expected: 10 well-organized commits, one per issue

- [ ] **Step 4: Commit if any final cleanup needed**

```bash
git add -A && git diff --cached --stat
```
If nothing unexpected, no extra commit needed.
