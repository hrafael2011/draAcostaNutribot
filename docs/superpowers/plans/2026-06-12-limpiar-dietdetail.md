# Limpiar DietDetail + Simplificar + Recalcular Nutrición — Implementation Plan

> **For agentic workers:** Use superpowers:subagent-driven-development (recommended) to implement this plan task-by-task.

**Goal:** Clean DietDetail of all technical jargon, hide advanced features behind flags, and recalculate nutrition engine after meal edits.

**Architecture:** 4 independent tasks — DietDetail rewrite, DietActions cleanup, feature flags for advanced strategies, and backend nutrition recalculation after meal edits.

**Tech Stack:** React 19, TypeScript, Tailwind CSS v4, FastAPI, SQLAlchemy async

**Spec:** [2026-06-12-limpiar-dietdetail.md](../specs/2026-06-12-limpiar-dietdetail.md)

---

## File Map

| File | Action | Responsibility |
|------|--------|---------------|
| `frontend/src/pages/DietDetail.tsx` | Rewrite | Remove all technical sections, inline styles, use DietPreviewPanel only |
| `frontend/src/components/diet/DietActions.tsx` | Modify | Remove Regenerate button |
| `frontend/src/types/index.ts` | Modify | Add `advancedStrategies` feature flag |
| `frontend/src/pages/DietWizard.tsx` | Modify | Hide Guided/Manual behind flag |
| `frontend/src/pages/Diets.tsx` | Modify | Hide strategy selectors behind flag |
| `backend/app/services/diet_service.py` | Modify | Re-run nutrition engine after meal edits |

---

### Task 1: Clean DietDetail — Remove all technical sections

**Files:** Modify: `frontend/src/pages/DietDetail.tsx`

**Context:** The current DietDetail page (recently modified to add editing support) still shows:
- `Patient #7` link
- `Status: generated · Updated 2026-06-12T18:10:25.594197Z`
- Inline style buttons: `Download .txt`, `Download .json`, `Download PDF`
- `Summary` heading in English
- `Versions` section with version history
- `Structured plan (JSON)` pre block
- `Regenerate (new version)` form with inline styles and strategy selectors

The `DietPreviewPanel` already handles all the good UI (title, status badge, nutrition summary, meal plan, DietActions with PDF/edit). The DietDetail page should just wrap it with breadcrumbs + date info.

**What to do:**

Read the current file first. Then rewrite the return JSX (everything after the last handler function) to only show:

```tsx
return (
  <div className="max-w-[900px] mx-auto">
    {/* Breadcrumb */}
    <div className="mb-4">
      <Link to="/diets" className="text-sm text-slate-500 hover:text-slate-700 transition-colors">
        ← Dietas
      </Link>
      <span className="mx-2 text-slate-300">/</span>
      <span className="text-sm text-slate-700 font-medium">
        {diet.title || "Plan Nutricional"}
      </span>
      {diet.patient_id && (
        <>
          <span className="mx-2 text-slate-300">/</span>
          <Link
            to={`/patients/${diet.patient_id}`}
            className="text-sm text-slate-500 hover:text-emerald-600 transition-colors"
          >
            Paciente #{diet.patient_id}
          </Link>
        </>
      )}
    </div>

    {/* Status + Date */}
    <div className="flex items-center gap-3 mb-6">
      <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ring-1 ring-inset ${
        diet.status === "pending_approval"
          ? "bg-amber-50 text-amber-700 ring-amber-600/20"
          : "bg-emerald-50 text-emerald-700 ring-emerald-600/20"
      }`}>
        {diet.status === "pending_approval" ? "Pendiente de aprobación" : "Aprobada"}
      </span>
      <span className="text-sm text-slate-400">
        {diet.updated_at
          ? new Date(diet.updated_at).toLocaleDateString("es-VE", {
              day: "numeric",
              month: "long",
              year: "numeric",
            })
          : ""}
      </span>
    </div>

    {/* Error / Message */}
    {error && (
      <div className="mb-4 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{error}</div>
    )}
    {msg && (
      <div className="mb-4 rounded-lg bg-emerald-50 px-3 py-2 text-sm text-emerald-700">{msg}</div>
    )}

    {/* DietPreviewPanel with editing + approve/discard */}
    <DietPreviewPanel
      diet={diet}
      editable={editing}
      onMealSave={handleMealSave}
      onToggleEdit={handleToggleEdit}
      onApprove={() => {
        import("../services/api").then(({ approveDiet }) =>
          approveDiet(diet.id).then((d) => {
            setDiet(d)
            addToast("Dieta aprobada", "success")
          })
        )
      }}
      onDiscard={() => {
        import("../services/api").then(({ discardDiet }) =>
          discardDiet(diet.id).then((d) => {
            setDiet(d)
            addToast("Dieta descartada", "success")
          })
        )
      }}
    />
  </div>
)
```

**Also remove from the component:**
- All inline style objects (inputStyle, selectStyle, etc.) if any remain
- `onExport` handler
- `onPdf` handler (already in DietActions)
- `onRegenerate` handler
- `regenDuration`, `mealsPerDay`, `strategyMode`, `dietStyle`, `macroProtein`, `macroCarbs`, `macroFat`, `manualKcal`, `manualProteinG`, `manualCarbsG`, `manualFatG` state variables (no longer needed for regenerate form)
- `instr` state
- `durationPresets` state
- `versions` state
- `buildDietStrategyBody`, `DurationPresetButtons`, `getDietVersions`, `getPlanDurationPresets`, `regenerateDiet`, `getDietVersions`, `downloadDietExport`, `downloadDietPdf` imports
- `DietVersion` type import
- All regenerate-related imports and utils

**Keep:**
- `diet` state, `error`, `msg`, `editing`
- `refresh` function (for initial load and after approve/discard)
- `handleToggleEdit`
- `handleMealSave`
- `useDietGeneration` (for editMeals)
- `useToast`
- `DietPreviewPanel` import

**After changes:**
- Run `cd frontend && npx tsc --noEmit` — fix any errors
- Run `cd frontend && npx vite build` — verify build succeeds
- Commit: `feat: clean DietDetail - remove technical sections, JSON, versions, regenerate form`

---

### Task 2: Remove Regenerate button from DietActions

**Files:** Modify: `frontend/src/components/diet/DietActions.tsx`

**Context:** The `DietActions` component currently shows "Regenerar (nueva versión)" button for `generated` status diets. This should be removed — regenerating is a separate feature for a future version.

**Changes:**

1. Remove the `onRegenerate` prop from the Props type
2. Remove the Regenerate button from the `status === "pending_approval"` block (line ~46):
   ```tsx
   // REMOVE this block:
   <Button variant="ghost" onClick={onRegenerate} disabled={loading} className="w-full text-sm">
     🔄 Regenerar
   </Button>
   ```
3. Remove the Regenerate button from the `status === "generated"` block (line ~70):
   ```tsx
   // REMOVE this block:
   <Button variant="ghost" onClick={onRegenerate} className="w-full text-sm">
     🔄 Regenerar (nueva versión)
   </Button>
   ```
4. Remove `onRegenerate` from the destructured props

**After changes:**
- Run `cd frontend && npx tsc --noEmit` — fix errors (DietPreviewPanel also passes onRegenerate, update it)
- Commit: `feat: remove Regenerate button from DietActions (future feature)`

---

### Task 3: Hide advanced strategies behind feature flag

**Files:** Modify: `frontend/src/types/index.ts`, `frontend/src/pages/DietWizard.tsx`, `frontend/src/pages/Diets.tsx`

**Context:** Guided and Manual strategy modes should be hidden behind `NEXT_FEATURES.advancedStrategies`. When false, only Auto mode is available and the wizard skips strategy-related steps.

**Step 1: Add feature flag to types/index.ts**

Read the current `NEXT_FEATURES` export and add the new flag:

```ts
export const NEXT_FEATURES = {
  batchDiets: false,
  advancedStrategies: false,  // Guided + Manual strategy modes
  regenerate: false,           // Regenerate diet feature
} as const;
```

**Step 2: Update DietWizard.tsx**

In the `stepOrder` array (line ~115), conditionally include strategy-related steps:

```tsx
const stepOrder: WizardStep[] = NEXT_FEATURES.advancedStrategies
  ? ["patient", "note", "duration", "meals", "strategy", "confirm", "preview"]
  : ["patient", "note", "duration", "meals", "confirm", "preview"];
```

In `goNext` (line ~120), only route to guided/manual steps when flag is on:

```tsx
const goNext = useCallback(() => {
  if (currentIndex < stepOrder.length - 1) {
    const next = stepOrder[currentIndex + 1]
    if (NEXT_FEATURES.advancedStrategies && next === "confirm" && state.strategyMode === "guided" && !state.dietStyle) {
      setStep("guided_style")
    } else if (NEXT_FEATURES.advancedStrategies && next === "confirm" && state.strategyMode === "guided" && state.dietStyle) {
      setStep("guided_macros")
    } else if (NEXT_FEATURES.advancedStrategies && next === "confirm" && state.strategyMode === "manual") {
      setStep("manual_targets")
    } else {
      setStep(next)
    }
  }
}, [currentIndex, state.strategyMode, state.dietStyle])
```

**Step 3: Update Diets.tsx inline form**

When `NEXT_FEATURES.advancedStrategies` is false, hide:
- Strategy mode selector (currently at ~line 554)
- Diet style selector (~line 597)
- Macro preferences section (~line 618)
- Manual targets section (~line 656)

Wrap each of these blocks in:
```tsx
{NEXT_FEATURES.advancedStrategies && (
  <div>...existing selector...</div>
)}
```

**After changes:**
- Run `cd frontend && npx tsc --noEmit` — verify clean
- Commit: `feat: hide advanced strategy modes behind NEXT_FEATURES.advancedStrategies flag`

---

### Task 4: Recalculate macros via GPT after meal edits

**Files:** Modify: `backend/app/services/diet_service.py`, `backend/app/services/diet_openai.py`

**Context:** When a doctor edits meals in a diet, the macros (protein_g, carbs_g, fat_g, daily_calories) should be recalculated based on the actual food items now in the plan. 

**Approach (Option C):** Call GPT with all meal texts from all days, ask it to estimate total daily macros as JSON. GPT knows food composition. Cost ~$0.001 per recalc, speed ~2 seconds.

**Step 1: Add `recalculate_macros` function to diet_openai.py**

```python
async def recalculate_macros_from_meals(
    plan: dict[str, Any],
    meals_per_day: int = 4,
) -> dict[str, Any]:
    """Ask GPT to estimate macros from the current meal plan text."""
    if not settings.OPENAI_API_KEY:
        return plan

    client = AsyncOpenAI(
        api_key=settings.OPENAI_API_KEY,
        base_url=settings.OPENAI_BASE_URL,
    )

    # Collect all meal texts
    days = plan.get("days", [])
    meal_summary_parts = []
    for day in days[:7]:
        if isinstance(day, dict):
            meals = day.get("meals", {})
            for slot, text in meals.items():
                if text:
                    meal_summary_parts.append(f"- {slot}: {text}")

    if not meal_summary_parts:
        return plan

    meal_texts = "\n".join(meal_summary_parts)

    prompt = f"""Eres nutricionista. A partir de este plan de comidas diario ({meals_per_day} comidas/día),
estima los macros totales diarios y calorías totales diarias.

Plan de comidas (1 día típico):
{meal_texts}

Responde SOLO con JSON válido en este formato exacto:
{{"daily_calories": 1800, "protein_g": 120.5, "carbs_g": 180.0, "fat_g": 55.0}}

Sé preciso con las cantidades. Usa gramos con 1 decimal. Las calorías deben ser coherentes con los macros (protein×4 + carbs×4 + fat×9)."""

    try:
        resp = await client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.2,
            max_tokens=150,
        )
        content = resp.choices[0].message.content
        if content:
            macros = json.loads(content.strip())
            plan["daily_calories"] = macros.get("daily_calories", plan.get("daily_calories"))
            plan["macro_grams"] = {
                "protein_g": macros.get("protein_g"),
                "carbs_g": macros.get("carbs_g"),
                "fat_g": macros.get("fat_g"),
            }
            # Recalculate percentages
            p = macros.get("protein_g", 0) * 4
            c = macros.get("carbs_g", 0) * 4
            f = macros.get("fat_g", 0) * 9
            total = p + c + f or 1
            plan["macro_percentages"] = {
                "protein": round(p / total * 100, 1),
                "carbs": round(c / total * 100, 1),
                "fat": round(f / total * 100, 1),
            }
            plan["macros_recalculated"] = True
            plan["macros_recalculated_at"] = utcnow().isoformat()
    except Exception:
        pass  # Keep existing macros if recalculation fails

    return plan
```

**Step 2: Call from `update_diet_meals`**

In `diet_service.py`, after the meal update loop and before setting `diet.structured_plan_json = plan`, add:

```python
# Recalculate macros based on edited meals
try:
    meals_per_day = plan.get("meals_per_day", 4)
    plan = await recalculate_macros_from_meals(plan, meals_per_day=meals_per_day)
except Exception:
    pass
```

**Step 3: Add import**

In `diet_service.py`, add:
```python
from app.services.diet_openai import generate_diet_plan_json, recalculate_macros_from_meals
```

(check existing import line, change to add the new function)

**After changes:**
- TypeScript check: `cd frontend && npx tsc --noEmit`
- Restart backend and test: edit a meal → save → verify nutrition summary shows updated macros
- Commit: `feat: recalculate macros via GPT after meal edits`

---

## Verification

- [ ] `cd frontend && npx tsc --noEmit` — no errors
- [ ] `cd frontend && npx vite build` — builds successfully
- [ ] Open DietDetail: no `Patient #7`, no JSON, no Versions, no Regenerate form
- [ ] Status shows "Aprobada" / "Pendiente de aprobación" badge
- [ ] Date shows "12 de junio de 2026" format
- [ ] No `Download .txt` / `Download .json` buttons
- [ ] Wizard only shows Auto mode (no strategy step)
- [ ] Edit a meal → nutrition summary updates with recalculated values
