# Unificar Formulario + Rediseño PublicIntake + Fix Responsive — Plan

> **For agentic workers:** Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans.

**Goal:** Unify intake form creation into a single button with dropdown, redesign PublicIntake with Tailwind/Spanish/cards, and fix responsive issues.

**Architecture:** Three independent frontend-only changes in 4 files. No backend changes.

**Tech Stack:** React 19, Tailwind CSS v4, TypeScript

**Spec:** `docs/superpowers/specs/2026-06-15-unificar-formulario-rediseno-public-intake.md`

---

### Task 1: Fix responsive — HeightInput and WeightInput

**Files:**
- Modify: `frontend/src/components/ui/HeightInput.tsx`
- Modify: `frontend/src/components/ui/WeightInput.tsx`

- [ ] **Step 1: Fix HeightInput ft/in mode on mobile**

In HeightInput.tsx, add responsive classes to the ft/in container:
```tsx
// Change the ft/in inner div from:
<div className="flex gap-1.5 flex-1">
// To:
<div className="flex gap-1.5 flex-1 flex-wrap">
```

This allows the ft and in inputs to wrap onto two lines on very narrow screens instead of overflowing.

- [ ] **Step 2: Fix WeightInput on mobile**

In WeightInput.tsx, change the outer div to allow wrapping:
```tsx
// Change:
<div className="flex gap-2">
// To:
<div className="flex gap-2 flex-wrap">
```

- [ ] **Step 3: Verify TS and commit**

```bash
cd frontend && npx tsc --noEmit && git add frontend/src/components/ui/HeightInput.tsx frontend/src/components/ui/WeightInput.tsx && git commit -m "fix: add flex-wrap to HeightInput and WeightInput for mobile responsive"
```

---

### Task 2: Unificar botones en IntakeLinks

**Files:**
- Modify: `frontend/src/pages/IntakeLinks.tsx`

- [ ] **Step 1: Remove the two separate buttons and replace with a single button + dropdown**

Replace lines 202-220 (the two buttons "Nuevo Formulario" + "Registro Rápido") with:

```tsx
<div className="relative">
  <button
    type="button"
    onClick={() => setShowFormDropdown(!showFormDropdown)}
    className="flex items-center gap-2 rounded-full bg-emerald-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-emerald-700 transition-colors shadow-sm"
  >
    <Plus size={18} weight="bold" />
    Nuevo Formulario
    <CaretDown size={14} weight="bold" className={`transition-transform ${showFormDropdown ? "rotate-180" : ""}`} />
  </button>

  {showFormDropdown && (
    <>
      <div className="fixed inset-0 z-40" onClick={() => setShowFormDropdown(false)} />
      <div className="absolute left-0 top-full mt-2 z-50 w-72 bg-white rounded-2xl shadow-xl border border-slate-200 py-2 overflow-hidden">
        <button
          type="button"
          onClick={() => { setShowFormDropdown(false); handleCreateRegisterLink(); }}
          className="flex items-start gap-3 w-full px-4 py-3 text-left hover:bg-emerald-50 transition-colors"
        >
          <span className="text-xl mt-0.5">📝</span>
          <div>
            <p className="text-sm font-semibold text-slate-800">Registro</p>
            <p className="text-xs text-slate-500">Para paciente nuevo — se crea automáticamente</p>
          </div>
        </button>
        <div className="border-t border-slate-100" />
        <button
          type="button"
          onClick={() => { setShowFormDropdown(false); handleStartCreate(); }}
          className="flex items-start gap-3 w-full px-4 py-3 text-left hover:bg-emerald-50 transition-colors"
        >
          <span className="text-xl mt-0.5">🔄</span>
          <div>
            <p className="text-sm font-semibold text-slate-800">Actualización</p>
            <p className="text-xs text-slate-500">Para paciente existente — elige quién</p>
          </div>
        </button>
      </div>
    </>
  )}
</div>
```

Add state: `const [showFormDropdown, setShowFormDropdown] = useState(false)`
Add import: `CaretDown` from `@phosphor-icons/react`

- [ ] **Step 2: Verify TS and commit**

```bash
cd frontend && npx tsc --noEmit && git add frontend/src/pages/IntakeLinks.tsx && git commit -m "feat: unify form creation into single button with dropdown"
```

---

### Task 3: Rediseño completo de PublicIntake — migrar a Tailwind + español + cards

**Files:**
- Modify: `frontend/src/pages/PublicIntake.tsx`

This is the largest change. The entire file needs to be rewritten from inline CSSProperties to Tailwind CSS.

- [ ] **Step 1: Rewrite the file**

Replace the entire `return` JSX block. The new layout:

- Wrapper: `max-w-2xl mx-auto px-4 py-8`
- Card container: `bg-white rounded-2xl shadow-sm border border-slate-100 p-6 md:p-8 space-y-8`
- Section headers: `text-xs font-semibold text-emerald-600 uppercase tracking-wider mb-4`
- Labels: `block text-sm font-medium text-slate-700 mb-1.5`
- Required marker: `<span className="text-red-500 ml-0.5">*</span>`
- Grid for name/email etc: `grid grid-cols-1 sm:grid-cols-2 gap-4`
- Footer privacy: `text-xs text-slate-400 text-center`

Structure:
```
┌─ Card ──────────────────────────────┐
│                                     │
│  Registro de Paciente               │
│  Completa tus datos...              │
│                                     │
│  ── DATOS PERSONALES ──            │
│  ┌──────────┐ ┌──────────┐         │
│  │ Nombre * │ │ Apellido*│         │
│  └──────────┘ └──────────┘         │
│  ┌────────────────────────────────┐ │
│  │ Fecha de nacimiento *          │ │
│  └────────────────────────────────┘ │
│  ...                               │
│                                     │
│  ── SALUD Y OBJETIVO ──           │
│  ...                               │
│                                     │
│  ── HÁBITOS ──                     │
│  ...                               │
│                                     │
│  [Enviar registro]                  │
│  🔒 Tus datos están protegidos...   │
└─────────────────────────────────────┘
```

Key translations:
- "Personal" → "Datos personales"
- "Measurements" → "Medidas corporales"
- "Goals & health" → "Salud y objetivo"
- "Habits" → "Hábitos"
- All field labels to Spanish
- "Submit" → "Enviar registro" / "Actualizar datos"
- Validation messages to Spanish

Remove the `CSSProperties` type import and the `wrap`/`input` style objects.

Keep the existing controlled state, DatePicker, NoAplicaField, WeightInput, HeightInput, and OBJECTIVE_OPTIONS imports. The logic stays the same — only the visual rendering changes.

- [ ] **Step 2: Verify TS**

```bash
cd frontend && npx tsc --noEmit
```

Expected: no errors. Fix any import issues (e.g., remove unused CSSProperties import).

- [ ] **Step 3: Commit**

```bash
git add frontend/src/pages/PublicIntake.tsx && git commit -m "feat: redesign PublicIntake with Tailwind, Spanish, cards, required indicators"
```

---

### Task 4: Build verification

- [ ] **Step 1: Full build**

```bash
cd frontend && npm run build
```

- [ ] **Step 2: Save plan to docs**

```bash
cp "/home/hendrick-rafael/.claude/plans/nesecito-hacer-unos-cambios-lovely-fountain.md" "/home/hendrick-rafael/Desktop/Proyectos Oficiales/diet_telegram_agent/docs/superpowers/plans/2026-06-15-unificar-formulario-rediseno-public-intake.md"
```

- [ ] **Step 3: Commit final**

```bash
git add docs/superpowers/plans/ && git commit -m "chore: final adjustments"
```

---

## Verification

| # | Check | How |
|---|-------|-----|
| 1 | Single button "Nuevo Formulario" with dropdown | Visit /formularios |
| 2 | Dropdown shows "Registro" and "Actualización" options | Click the button |
| 3 | PublicIntake in Spanish with cards and asterisks | Open registration link |
| 4 | Required fields have `*` marker | Check labels in form |
| 5 | Update form shows only allowed fields | Open update link |
| 6 | HeightInput ft/in wraps correctly on mobile | Resize browser narrow |
| 7 | Build passes | `npm run build` |
