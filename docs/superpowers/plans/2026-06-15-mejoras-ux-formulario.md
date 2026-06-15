# UX Form Improvements — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement 4 UX improvements across patient forms: DatePicker with fast year navigation, unified objective options, "No aplica" checkbox for clinical fields, and weight/height unit toggles in admin forms.

**Architecture:** Install `react-day-picker` v9 for the date picker. Create 4 reusable UI components (`DatePicker`, `NoAplicaField`, `WeightInput`, `HeightInput`) and 1 constants file (`objectives.ts`). Modify 3 form pages to use the new components. All components support both controlled React state (PatientDrawer, PatientDetail) and native FormData (PublicIntake).

**Tech Stack:** React 19, TypeScript 5.7, Tailwind CSS v4, react-day-picker v9, framer-motion (existing)

**Spec:** `docs/superpowers/specs/2026-06-15-mejoras-ux-formulario.md`

---

### Task 1: Install react-day-picker dependency

**Files:**
- Modify: `frontend/package.json`

- [ ] **Step 1: Install react-day-picker v9**

```bash
cd frontend && npm install react-day-picker@^9
```

- [ ] **Step 2: Verify installation**

```bash
cd frontend && node -e "require('react-day-picker'); console.log('OK')"
```

Expected: prints "OK" with no errors.

- [ ] **Step 3: Commit**

```bash
git add frontend/package.json frontend/package-lock.json
git commit -m "chore: install react-day-picker v9 for date picker component"
```

---

### Task 2: Create shared objectives constant

**Files:**
- Create: `frontend/src/constants/objectives.ts`

- [ ] **Step 1: Create the constants file**

```typescript
// frontend/src/constants/objectives.ts

export const OBJECTIVE_OPTIONS: { value: string; label: string }[] = [
  { value: "", label: "Sin especificar" },
  { value: "lose_weight", label: "⬇️  Bajar de peso" },
  { value: "fat_loss", label: "🔥  Pérdida de grasa" },
  { value: "muscle_gain", label: "💪  Ganancia muscular" },
  { value: "gain_weight", label: "⬆️  Subir de peso" },
  { value: "maintenance", label: "⚖️  Mantenimiento" },
  { value: "health_improvement", label: "❤️  Mejora de salud" },
  { value: "sports_performance", label: "🏃  Rendimiento deportivo" },
];
```

- [ ] **Step 2: Verify file compiles**

```bash
cd frontend && npx tsc --noEmit src/constants/objectives.ts
```

Expected: no errors.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/constants/objectives.ts
git commit -m "feat: add shared OBJECTIVE_OPTIONS constant with 7 unified options"
```

---

### Task 3: Create DatePicker component

**Files:**
- Create: `frontend/src/components/ui/DatePicker.tsx`
- Reference: `frontend/src/components/ui/Button.tsx` (for style patterns)

- [ ] **Step 1: Create DatePicker component**

```tsx
// frontend/src/components/ui/DatePicker.tsx
import { useState, useRef, useEffect } from "react";
import { DayPicker, type DateRange } from "react-day-picker";
import "react-day-picker/style.css";

type DatePickerProps = {
  value: string;             // ISO date string "YYYY-MM-DD" or ""
  onChange: (iso: string) => void;
  name?: string;             // for FormData-based forms
  placeholder?: string;
  required?: boolean;
};

export default function DatePicker({
  value,
  onChange,
  name,
  placeholder = "DD/MM/AAAA",
  required = false,
}: DatePickerProps) {
  const [open, setOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  const selected = value ? new Date(value + "T00:00:00") : undefined;

  const displayText = value
    ? new Date(value + "T00:00:00").toLocaleDateString("es-ES", {
        day: "2-digit",
        month: "2-digit",
        year: "numeric",
      })
    : "";

  // Close on outside click
  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    if (open) document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, [open]);

  function handleSelect(
    day: Date | undefined,
    _triggerDate: Date,
    _modifiers: any,
    _e: React.MouseEvent | React.KeyboardEvent | React.ChangeEvent,
  ) {
    if (day) {
      const iso = day.toISOString().slice(0, 10);
      onChange(iso);
      setOpen(false);
    }
  }

  return (
    <div ref={containerRef} className="relative">
      {/* Trigger */}
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="w-full flex items-center gap-2 px-3.5 py-2.5 text-sm border border-slate-200 rounded-xl bg-white text-slate-800 hover:border-emerald-400 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-colors text-left"
      >
        <span className="text-slate-400 text-base">📅</span>
        <span className={value ? "text-slate-800" : "text-slate-400"}>
          {displayText || placeholder}
        </span>
      </button>

      {/* Hidden native input for FormData compatibility */}
      {name && (
        <input type="hidden" name={name} value={value} required={required} />
      )}

      {/* Popover */}
      {open && (
        <div className="absolute z-50 mt-1 bg-white border border-slate-200 rounded-2xl shadow-xl p-3">
          <DayPicker
            mode="single"
            selected={selected}
            onSelect={(d: Date | undefined) =>
              handleSelect(
                d,
                new Date(),
                {},
                {} as React.ChangeEvent,
              )
            }
            captionLayout="dropdown"
            defaultMonth={selected || new Date(1990, 0)}
            startMonth={new Date(1920, 0)}
            endMonth={new Date()}
            showOutsideDays={false}
            style={{
              "--rdp-accent-color": "#10b981",
              "--rdp-accent-background-color": "#d1fae5",
            } as React.CSSProperties}
          />
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 2: Verify TypeScript compilation**

```bash
cd frontend && npx tsc --noEmit
```

Expected: no TS errors (may have pre-existing errors, but no NEW errors from DatePicker.tsx).

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/ui/DatePicker.tsx
git commit -m "feat: add DatePicker component with react-day-picker + month/year dropdowns"
```

---

### Task 4: Create NoAplicaField component

**Files:**
- Create: `frontend/src/components/ui/NoAplicaField.tsx`

- [ ] **Step 1: Create NoAplicaField component**

```tsx
// frontend/src/components/ui/NoAplicaField.tsx
import { type ChangeEvent } from "react";

type NoAplicaFieldProps = {
  label: string;
  value: string;
  onChange: (value: string) => void;
  name?: string;            // for FormData-based forms
  placeholder?: string;
  naLabel?: string;
  required?: boolean;
  type?: "textarea" | "input";
  rows?: number;
};

const INPUT_CLASS =
  "w-full px-3.5 py-2.5 text-sm border border-slate-200 rounded-xl bg-white text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-colors";

export default function NoAplicaField({
  label,
  value,
  onChange,
  name,
  placeholder,
  naLabel = "No aplica",
  required = false,
  type = "textarea",
  rows = 2,
}: NoAplicaFieldProps) {
  const checked = value === "No aplica";

  function handleCheckboxChange(e: ChangeEvent<HTMLInputElement>) {
    if (e.target.checked) {
      onChange("No aplica");
    } else {
      onChange("");
    }
  }

  function handleTextChange(
    e: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>,
  ) {
    onChange(e.target.value);
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-1.5">
        <label className="text-sm font-medium text-slate-700">
          {label}
          {required && <span className="text-red-500 ml-0.5">*</span>}
        </label>
        <label className="flex items-center gap-1.5 cursor-pointer select-none">
          <input
            type="checkbox"
            checked={checked}
            onChange={handleCheckboxChange}
            className="rounded border-slate-300 text-emerald-600 focus:ring-emerald-500/20 w-4 h-4"
          />
          <span
            className={`text-xs font-medium ${checked ? "text-emerald-600" : "text-slate-500"}`}
          >
            {naLabel}
          </span>
        </label>
      </div>

      {type === "textarea" ? (
        <textarea
          name={!checked ? name : undefined}
          value={checked ? "" : value}
          onChange={handleTextChange}
          disabled={checked}
          rows={rows}
          placeholder={checked ? "No aplica" : placeholder}
          className={`${INPUT_CLASS} resize-none ${checked ? "bg-slate-50 text-slate-400 opacity-60 cursor-not-allowed" : ""}`}
          required={required && !checked}
        />
      ) : (
        <input
          type="text"
          name={!checked ? name : undefined}
          value={checked ? "" : value}
          onChange={handleTextChange}
          disabled={checked}
          placeholder={checked ? "No aplica" : placeholder}
          className={`${INPUT_CLASS} ${checked ? "bg-slate-50 text-slate-400 opacity-60 cursor-not-allowed" : ""}`}
          required={required && !checked}
        />
      )}

      {/* Hidden input to send "No aplica" value in FormData when checked */}
      {name && checked && <input type="hidden" name={name} value="No aplica" />}
    </div>
  );
}
```

- [ ] **Step 2: Verify compilation**

```bash
cd frontend && npx tsc --noEmit
```

Expected: no new TS errors.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/ui/NoAplicaField.tsx
git commit -m "feat: add NoAplicaField component with checkbox that disables textarea/input"
```

---

### Task 5: Create WeightInput component

**Files:**
- Create: `frontend/src/components/ui/WeightInput.tsx`

- [ ] **Step 1: Create WeightInput component**

```tsx
// frontend/src/components/ui/WeightInput.tsx
import { useState, type ChangeEvent } from "react";

export const WEIGHT_LB_TO_KG = 0.45359237;

type WeightInputProps = {
  valueKg: string;           // controlled value always in kg (string for form compatibility)
  onChangeKg: (kg: string) => void;
  name?: string;             // for FormData — sends kg value
  required?: boolean;
  placeholder?: string;
};

const INPUT_CLASS =
  "flex-1 px-3.5 py-2.5 text-sm border border-slate-200 rounded-xl bg-white text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-colors";

export default function WeightInput({
  valueKg,
  onChangeKg,
  name,
  required = false,
  placeholder = "0.0",
}: WeightInputProps) {
  const kg = parseFloat(valueKg);
  const [unit, setUnit] = useState<"kg" | "lb">("kg");

  // Recalculate display value when unit changes
  const displayValue = (() => {
    if (!valueKg || isNaN(kg)) return "";
    if (unit === "kg") return valueKg;
    return (kg / WEIGHT_LB_TO_KG).toFixed(1);
  })();

  function handleValueChange(e: ChangeEvent<HTMLInputElement>) {
    const raw = e.target.value;
    if (raw === "" || raw === "-") {
      onChangeKg("");
      return;
    }
    const num = parseFloat(raw);
    if (isNaN(num)) return;
    const kgValue = unit === "kg" ? num : num * WEIGHT_LB_TO_KG;
    onChangeKg(kgValue.toFixed(2));
  }

  function handleUnitChange(e: ChangeEvent<HTMLSelectElement>) {
    setUnit(e.target.value as "kg" | "lb");
  }

  return (
    <div className="flex gap-2">
      <input
        type="number"
        step="0.1"
        min="0"
        value={displayValue}
        onChange={handleValueChange}
        placeholder={placeholder}
        className={INPUT_CLASS}
        required={required}
      />
      <select
        value={unit}
        onChange={handleUnitChange}
        className="px-2 py-2.5 text-sm border border-slate-200 rounded-xl bg-white text-slate-700 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-colors shrink-0"
      >
        <option value="kg">kg</option>
        <option value="lb">lb</option>
      </select>
      {/* Hidden input sends kg value for FormData */}
      {name && <input type="hidden" name={name} value={valueKg} />}
    </div>
  );
}

- [ ] **Step 2: Fix React import and verify compilation**

```bash
cd frontend && npx tsc --noEmit
```

Expected: no new TS errors.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/ui/WeightInput.tsx
git commit -m "feat: add WeightInput component with kg/lb toggle"
```

---

### Task 6: Create HeightInput component

**Files:**
- Create: `frontend/src/components/ui/HeightInput.tsx`

- [ ] **Step 1: Create HeightInput component**

```tsx
// frontend/src/components/ui/HeightInput.tsx
import { useState, type ChangeEvent } from "react";

export const IN_TO_CM = 2.54;

type HeightInputProps = {
  valueCm: string;           // controlled value always in cm
  onChangeCm: (cm: string) => void;
  name?: string;             // for FormData — sends cm value
  required?: boolean;
  placeholder?: string;
};

const INPUT_CLASS =
  "flex-1 px-3.5 py-2.5 text-sm border border-slate-200 rounded-xl bg-white text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-colors";

export default function HeightInput({
  valueCm,
  onChangeCm,
  name,
  required = false,
  placeholder = "0",
}: HeightInputProps) {
  const [unit, setUnit] = useState<"cm" | "ftin">("cm");
  const cm = parseFloat(valueCm);

  // Display values
  const displayCm = unit === "cm" && valueCm ? valueCm : "";
  const totalInches = !isNaN(cm) ? cm / IN_TO_CM : 0;
  const displayFt = unit === "ftin" && valueCm ? Math.floor(totalInches / 12).toString() : "";
  const displayIn = unit === "ftin" && valueCm ? Math.round(totalInches % 12).toString() : "";

  function handleCmChange(e: ChangeEvent<HTMLInputElement>) {
    const raw = e.target.value;
    if (raw === "" || raw === "-") {
      onChangeCm("");
      return;
    }
    const num = parseFloat(raw);
    if (isNaN(num)) return;
    onChangeCm(num.toFixed(1));
  }

  function handleFtInChange(ftStr: string, inStr: string) {
    const ft = parseFloat(ftStr) || 0;
    const inch = parseFloat(inStr) || 0;
    if (ft === 0 && inStr === "") {
      onChangeCm("");
      return;
    }
    const cmValue = (ft * 12 + inch) * IN_TO_CM;
    onChangeCm(cmValue.toFixed(1));
  }

  function handleUnitChange(e: ChangeEvent<HTMLSelectElement>) {
    setUnit(e.target.value as "cm" | "ftin");
  }

  return (
    <div className="flex gap-2 items-center">
      <select
        value={unit}
        onChange={handleUnitChange}
        className="px-2 py-2.5 text-sm border border-slate-200 rounded-xl bg-white text-slate-700 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-colors shrink-0"
      >
        <option value="cm">cm</option>
        <option value="ftin">ft/in</option>
      </select>
      {unit === "cm" ? (
        <input
          type="number"
          step="0.1"
          min="0"
          value={displayCm}
          onChange={handleCmChange}
          placeholder={placeholder}
          className={INPUT_CLASS}
          required={required}
        />
      ) : (
        <div className="flex gap-1.5 flex-1">
          <input
            type="number"
            step="1"
            min="0"
            max="8"
            value={displayFt}
            onChange={(e) => handleFtInChange(e.target.value, displayIn)}
            placeholder="ft"
            className={INPUT_CLASS}
            required={required}
          />
          <span className="text-xs text-slate-400 self-center shrink-0">ft</span>
          <input
            type="number"
            step="1"
            min="0"
            max="11"
            value={displayIn}
            onChange={(e) => handleFtInChange(displayFt, e.target.value)}
            placeholder="in"
            className={INPUT_CLASS}
          />
          <span className="text-xs text-slate-400 self-center shrink-0">in</span>
        </div>
      )}
      {/* Hidden input sends cm value for FormData */}
      {name && <input type="hidden" name={name} value={valueCm} />}
    </div>
  );
}
```

- [ ] **Step 2: Verify compilation**

```bash
cd frontend && npx tsc --noEmit
```

Expected: no new TS errors.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/ui/HeightInput.tsx
git commit -m "feat: add HeightInput component with cm ↔ ft/in toggle"
```

---

### Task 7: Update PatientDrawer with all 4 changes

**Files:**
- Modify: `frontend/src/components/patients/PatientDrawer.tsx`

This task updates the admin patient creation drawer:
1. Replace native date input with `<DatePicker>`
2. Replace inline OBJECTIVES array with import from constants
3. Replace clinical textareas with `<NoAplicaField>` for diseases, medications, food_allergies, foods_avoided
4. Replace weight/height inputs with `<WeightInput>` and `<HeightInput>`

- [ ] **Step 1: Update imports and remove inline OBJECTIVES array**

At the top of the file, add new imports:

```tsx
import DatePicker from "../../components/ui/DatePicker";
import NoAplicaField from "../../components/ui/NoAplicaField";
import WeightInput from "../../components/ui/WeightInput";
import HeightInput from "../../components/ui/HeightInput";
import { OBJECTIVE_OPTIONS } from "../../constants/objectives";
```

Remove lines 57-64 (the old `OBJECTIVES` constant definition).

- [ ] **Step 2: Replace birth date input (line 284-290)**

Replace:
```tsx
<input
  id="drawer-birth-date"
  type="date"
  value={form.birth_date}
  onChange={setField("birth_date")}
  className={INPUT_CLASS}
/>
```

With:
```tsx
<DatePicker
  value={form.birth_date}
  onChange={(iso) => setForm((prev) => ({ ...prev, birth_date: iso }))}
  placeholder="DD/MM/AAAA"
/>
```

- [ ] **Step 3: Replace objective select (lines 402-413)**

Replace the `<select>` that iterates `OBJECTIVES` with one that iterates `OBJECTIVE_OPTIONS`:

```tsx
<select
  id="drawer-objective"
  value={form.objective}
  onChange={setField("objective")}
  className={INPUT_CLASS}
>
  {OBJECTIVE_OPTIONS.map((o) => (
    <option key={o.value} value={o.value}>
      {o.label}
    </option>
  ))}
</select>
```

- [ ] **Step 4: Replace diseases textarea (lines 415-427)**

Replace:
```tsx
<div>
  <label htmlFor="drawer-diseases" className={LABEL_CLASS}>
    Enfermedades
  </label>
  <textarea
    id="drawer-diseases"
    value={form.diseases}
    onChange={setField("diseases")}
    rows={2}
    placeholder="Ej. Diabetes tipo 2, Hipertensión"
    className={INPUT_CLASS + " resize-none"}
  />
</div>
```

With:
```tsx
<NoAplicaField
  label="Enfermedades"
  value={form.diseases}
  onChange={(v) => setForm((prev) => ({ ...prev, diseases: v }))}
  placeholder="Ej. Diabetes tipo 2, Hipertensión"
/>
```

Repeat the same pattern for **medications** (lines 428-439), **food_allergies** (lines 441-452), and **foods_avoided** (lines 454-465). For each, use `<NoAplicaField>` with the corresponding form field.

- [ ] **Step 5: Replace weight input (lines 518-531)**

Replace:
```tsx
<div>
  <label htmlFor="drawer-weight" className={LABEL_CLASS}>
    Peso (kg)
  </label>
  <input ... />
</div>
```

With:
```tsx
<div>
  <label className={LABEL_CLASS}>Peso</label>
  <WeightInput
    valueKg={form.weight_kg}
    onChangeKg={(v) => setForm((prev) => ({ ...prev, weight_kg: v }))}
    placeholder="Ej. 70.5"
  />
</div>
```

- [ ] **Step 6: Replace height input (lines 533-546)**

Replace:
```tsx
<div>
  <label htmlFor="drawer-height" className={LABEL_CLASS}>
    Altura (cm)
  </label>
  <input ... />
</div>
```

With:
```tsx
<div>
  <label className={LABEL_CLASS}>Altura</label>
  <HeightInput
    valueCm={form.height_cm}
    onChangeCm={(v) => setForm((prev) => ({ ...prev, height_cm: v }))}
    placeholder="Ej. 170"
  />
</div>
```

- [ ] **Step 7: Verify TypeScript compilation**

```bash
cd frontend && npx tsc --noEmit
```

Expected: no new TS errors in PatientDrawer.tsx.

- [ ] **Step 8: Commit**

```bash
git add frontend/src/components/patients/PatientDrawer.tsx
git commit -m "feat: update PatientDrawer with DatePicker, unified objectives, NoAplica fields, unit toggles"
```

---

### Task 8: Update PublicIntake with all 4 changes

**Files:**
- Modify: `frontend/src/pages/PublicIntake.tsx`

This task updates the patient-facing intake form. Since PublicIntake uses FormData API + inline CSSProperties, the components need `name` props to participate in FormData.

- [ ] **Step 1: Add imports and controlled state for components**

Add imports at top:
```tsx
import DatePicker from "../components/ui/DatePicker";
import NoAplicaField from "../components/ui/NoAplicaField";
import WeightInput from "../components/ui/WeightInput";
import HeightInput from "../components/ui/HeightInput";
import { OBJECTIVE_OPTIONS } from "../constants/objectives";
```

Add state for controlled component values (needed because PublicIntake uses FormData, but components need controlled React state):

```tsx
// Add after existing state declarations (after line 25)
const [birthDate, setBirthDate] = useState("");
const [diseases, setDiseases] = useState("");
const [medications, setMedications] = useState("");
const [foodAllergies, setFoodAllergies] = useState("");
const [foodsAvoided, setFoodsAvoided] = useState("");
const [medicalHistory, setMedicalHistory] = useState("");
const [weightKg, setWeightKg] = useState("");
const [heightCm, setHeightCm] = useState("");
const [objective, setObjective] = useState("");
```

- [ ] **Step 2: Replace birth date input (line 192)**

Replace:
```tsx
<input name="birth_date" type="date" required style={input} />
```

With:
```tsx
<DatePicker
  value={birthDate}
  onChange={setBirthDate}
  name="birth_date"
  placeholder="DD/MM/AAAA"
  required
/>
```

- [ ] **Step 3: Replace objective free-text input (line 267)**

Replace:
```tsx
<input name="objective" required placeholder="e.g. lose_weight" style={input} />
```

With:
```tsx
<select
  name="objective"
  value={objective}
  onChange={(e) => setObjective(e.target.value)}
  required
  style={input}
>
  {OBJECTIVE_OPTIONS.map((o) => (
    <option key={o.value} value={o.value}>
      {o.label}
    </option>
  ))}
</select>
```

- [ ] **Step 4: Replace weight/height section (lines 226-251)**

Replace the weight unit select + weight input + height unit select + height inputs with:

```tsx
<label style={{ fontSize: 13 }}>Peso *</label>
<WeightInput
  valueKg={weightKg}
  onChangeKg={setWeightKg}
  name="weight_kg"
  required
/>

<label style={{ fontSize: 13, marginTop: 10 }}>Estatura *</label>
<HeightInput
  valueCm={heightCm}
  onChangeCm={setHeightCm}
  name="height_cm"
  required
/>
```

Remove the old `weightUnit` and `heightUnit` state (lines 24-25) since WeightInput and HeightInput manage their own units internally.

- [ ] **Step 5: Update submit handler**

In the `onSubmit` function, remove `weightUnit`, `heightUnit` references. Replace the old weight/height calculation logic (lines 60-77) with a simple parse of the controlled values (already in kg/cm):

```tsx
const weightKgNum = parseFloat(weightKg);
const heightCmNum = parseFloat(heightCm);

const weight_kg = !isNaN(weightKgNum) && weightKgNum > 0 ? weightKgNum : NaN;
const height_cm = !isNaN(heightCmNum) && heightCmNum > 0 ? heightCmNum : NaN;
```

Remove `weight_value`, `height_cm_value`, `height_ft_value`, `height_in_value` from the form — the hidden inputs in WeightInput/HeightInput handle this via `name="weight_kg"` and `name="height_cm"`.

Update the body object:
```tsx
const body: Record<string, unknown> = {
  first_name: str("first_name"),
  last_name: str("last_name"),
  birth_date: birthDate,
  sex: str("sex"),
  country,
  city: city || str("city_other"),
  objective: objective,
  food_allergies: foodAllergies === "No aplica" ? "No aplica" : foodAllergies,
  foods_avoided: foodsAvoided === "No aplica" ? "No aplica" : foodsAvoided,
  weight_kg: weight_kg,
  height_cm: height_cm,
  // ... rest unchanged
  diseases: diseases === "No aplica" ? "No aplica" : diseases,
  medications: medications === "No aplica" ? "No aplica" : medications,
  medical_history: medicalHistory === "No aplica" ? "No aplica" : medicalHistory,
  // ...
};
```

- [ ] **Step 6: Replace 5 clinical fields with NoAplicaField**

Replace diseases (line 268-269):
```tsx
<NoAplicaField
  label="Enfermedades / diagnósticos"
  value={diseases}
  onChange={setDiseases}
  name="diseases"
  placeholder="Ej. Diabetes tipo 2, Hipertensión"
/>
```

Replace medications (line 270-271):
```tsx
<NoAplicaField
  label="Medicamentos"
  value={medications}
  onChange={setMedications}
  name="medications"
  placeholder="Ej. Metformina 500mg"
/>
```

Replace food_allergies (line 272-273):
```tsx
<NoAplicaField
  label="Alergias alimentarias"
  value={foodAllergies}
  onChange={setFoodAllergies}
  name="food_allergies"
  type="input"
  placeholder="Ej. Gluten, lactosa"
/>
```

Replace foods_avoided (lines 274-275):
```tsx
<NoAplicaField
  label="Alimentos a evitar"
  value={foodsAvoided}
  onChange={setFoodsAvoided}
  name="foods_avoided"
  type="input"
  placeholder="Ej. Lácteos, gluten"
/>
```

Replace medical_history (lines 276-280):
```tsx
<NoAplicaField
  label="Historial médico"
  value={medicalHistory}
  onChange={setMedicalHistory}
  name="medical_history"
  placeholder="Incluye diagnósticos, cirugías, eventos relevantes..."
/>
```

- [ ] **Step 7: Verify TypeScript compilation**

```bash
cd frontend && npx tsc --noEmit
```

Expected: no new TS errors in PublicIntake.tsx.

- [ ] **Step 8: Commit**

```bash
git add frontend/src/pages/PublicIntake.tsx
git commit -m "feat: update PublicIntake with DatePicker, objective select, NoAplica fields, shared WeightInput/HeightInput"
```

---

### Task 9: Update PatientDetail with all 4 changes

**Files:**
- Modify: `frontend/src/pages/PatientDetail.tsx`

This task updates the patient detail/edit page. Changes:
1. Replace native date input with `<DatePicker>` in the demographic edit form
2. Update objective select to use `OBJECTIVE_OPTIONS` constant
3. Add `NoAplicaField` for medications textarea
4. Add `WeightInput`/`HeightInput` to the metric registration form

- [ ] **Step 1: Add imports**

Add at top of PatientDetail.tsx:
```tsx
import DatePicker from "../components/ui/DatePicker";
import NoAplicaField from "../components/ui/NoAplicaField";
import WeightInput from "../components/ui/WeightInput";
import HeightInput from "../components/ui/HeightInput";
import { OBJECTIVE_OPTIONS } from "../constants/objectives";
```

- [ ] **Step 2: Replace birth date input in edit form (line 843-848)**

Replace:
```tsx
<input
  name="birth_date"
  type="date"
  defaultValue={patient.birth_date?.slice(0, 10) ?? ""}
  className={INPUT_CLASSES}
/>
```

With a controlled DatePicker. Add state:
```tsx
const [editBirthDate, setEditBirthDate] = useState("");
```

And in the form:
```tsx
<DatePicker
  value={editBirthDate}
  onChange={setEditBirthDate}
  name="birth_date"
  placeholder="DD/MM/AAAA"
/>
```

Initialize `editBirthDate` from patient data in a useEffect or use the `dataFormKey` pattern to set initial value. Use the `key={dataFormKey}` prop on a wrapper to reset state when entering edit mode.

Actually, since PatientDetail uses FormData for its form submissions, we can use the `name` prop approach. But we also need controlled state for the DatePicker. Let's add a state variable and initialize it when entering edit mode.

```tsx
// Add state near other metric form states (around line 299)
const [editBirthDate, setEditBirthDate] = useState(patient.birth_date?.slice(0, 10) ?? "");
```

And replace lines 843-848 with:
```tsx
<DatePicker
  value={editBirthDate}
  onChange={setEditBirthDate}
  name="birth_date"
  placeholder="DD/MM/AAAA"
/>
```

Also update the `dataFormKey` reset logic: when `onClick` handler enters edit mode (line 651), also reset `editBirthDate`:
```tsx
onClick={() => {
  setDataFormKey((k) => k + 1)
  setProfileFormKey((k) => k + 1)
  setEditBirthDate(patient.birth_date?.slice(0, 10) ?? "")
  setEditingData(true)
  setEditingProfile(true)
}}
```

- [ ] **Step 3: Update objective select (lines 985-995)**

Replace the 4 hardcoded options:
```tsx
<select
  name="objective"
  defaultValue={profile?.objective ?? ""}
  className={SELECT_CLASSES}
>
  {OBJECTIVE_OPTIONS.map((o) => (
    <option key={o.value} value={o.value}>
      {o.label}
    </option>
  ))}
</select>
```

- [ ] **Step 4: Add NoAplicaField for medications textarea (line 1017-1022)**

Replace medications textarea:
```tsx
<textarea
  name="medications"
  rows={2}
  defaultValue={profile?.medications ?? ""}
  className={INPUT_CLASSES}
/>
```

With `<NoAplicaField>`. Add state for medications (near the PillSelect states):
```tsx
const [editMedications, setEditMedications] = useState(profile?.medications ?? "");
```

And in the form:
```tsx
<NoAplicaField
  label="Medicamentos"
  value={editMedications}
  onChange={setEditMedications}
  name="medications"
  placeholder="Ej. Metformina 500mg, Losartán 50mg"
/>
```

Initialize `editMedications` when entering edit mode similar to `editBirthDate`.

- [ ] **Step 5: Add WeightInput + HeightInput to metric form (lines 1377-1398)**

Replace the weight input (lines 1378-1386):
```tsx
<div>
  <label className="block text-xs font-medium text-slate-500 mb-1">
    Peso
  </label>
  <WeightInput
    valueKg={mWeight}
    onChangeKg={setMWeight}
    placeholder="ej. 65.0"
  />
</div>
```

Replace the height input (lines 1388-1397):
```tsx
<div>
  <label className="block text-xs font-medium text-slate-500 mb-1">
    Altura
  </label>
  <HeightInput
    valueCm={mHeight}
    onChangeCm={setMHeight}
    placeholder="ej. 162"
  />
</div>
```

Note: The metric form already submits kg/cm values, so `WeightInput`/`HeightInput` outputs match the expected API format directly.

- [ ] **Step 6: Verify TypeScript compilation**

```bash
cd frontend && npx tsc --noEmit
```

Expected: no new TS errors.

- [ ] **Step 7: Commit**

```bash
git add frontend/src/pages/PatientDetail.tsx
git commit -m "feat: update PatientDetail with DatePicker, unified objectives, NoAplica medications, WeightInput/HeightInput"
```

---

### Task 10: Build verification

**Files:**
- (none) - verification only

- [ ] **Step 1: Run TypeScript type check**

```bash
cd frontend && npx tsc --noEmit
```

Expected: no TypeScript errors. Fix any if present.

- [ ] **Step 2: Run frontend build**

```bash
cd frontend && npm run build
```

Expected: build succeeds with no errors.

- [ ] **Step 3: Quick smoke test**

Start the dev server and verify:
1. PatientDrawer: Date picker opens with month/year dropdowns, objective has 7 options, NoAplica fields toggle correctly, weight/height have unit toggles
2. PublicIntake: Same verifications
3. PatientDetail: Date picker works, objective has 7 options, medications has NoAplica, metric form has unit toggles

```bash
cd frontend && npm run dev
```

Open browser, navigate to each form, and verify the 4 changes work as expected.

- [ ] **Step 4: Final commit**

```bash
git add -A
git commit -m "chore: final adjustments and verification after UX form improvements"
```

---

## Verification Summary

After all tasks complete, verify:

| # | What to check | How |
|---|---------------|-----|
| 1 | `npx tsc --noEmit` passes | Terminal |
| 2 | `npm run build` succeeds | Terminal |
| 3 | DatePicker opens, month/year dropdowns navigate decades | Browser: click trigger |
| 4 | Objective select has 8 options (incl. empty) in all 3 forms | Browser: inspect options |
| 5 | NoAplica checkbox disables textarea | Browser: check then uncheck |
| 6 | Weight toggle kg↔lb converts correctly (154 lb ≈ 69.85 kg) | Browser: toggle, check value |
| 7 | Height toggle cm↔ft/in converts correctly (5'9" ≈ 175 cm) | Browser: toggle, check value |
| 8 | Existing patient data displays correctly | Browser: open existing patient |
