import { FormEvent, useCallback, useEffect, useState } from "react"
import { Link, useParams } from "react-router-dom"
import {
  downloadDietExport,
  downloadDietPdf,
  getDiet,
  getDietVersions,
  getPlanDurationPresets,
  regenerateDiet,
} from "../services/api"
import type { Diet, DietVersion } from "../types"
import { DurationPresetButtons } from "../components/DurationPresetButtons"
import {
  clampDurationDays,
  durationAdjustHint,
  FALLBACK_PLAN_DURATION_PRESETS,
  planDurationDaysFromPlanJson,
} from "../utils/duration"
import { buildDietStrategyBody } from "../utils/dietStrategyBody"
import { mealSlotsSummaryEs, resolveMealSlots } from "../utils/planMeals"
import type { DietStrategyMode, MealsPerDay } from "../types"

function NutritionEnginePanel({ plan }: { plan: unknown }) {
  if (!plan || typeof plan !== "object") return null
  const p = plan as Record<string, unknown>
  const ne = p.nutrition_engine
  const macroGrams = p.macro_grams
  const rules = p.clinical_rules_applied
  const alerts = p.alerts
  const hasNe = ne && typeof ne === "object" && Object.keys(ne as object).length > 0
  const hasMg = Boolean(
    macroGrams &&
      typeof macroGrams === "object" &&
      Object.values(macroGrams as Record<string, unknown>).some((v) => v != null),
  )
  const hasRules = Array.isArray(rules) && rules.length > 0
  const hasAlerts = Array.isArray(alerts) && alerts.length > 0
  const pdays = planDurationDaysFromPlanJson(p)
  const hasDur = pdays != null
  if (!hasNe && !hasMg && !hasRules && !hasAlerts && !hasDur) return null

  const neObj = hasNe ? (ne as Record<string, unknown>) : null

  return (
    <div
      style={{
        marginBottom: 24,
        padding: 16,
        background: "#f8f6fef0",
        border: "1px solid #e0d8cc",
        borderRadius: 8,
        lineHeight: 1.5,
      }}
    >
      <h2 style={{ fontSize: 16, marginTop: 0 }}>Motor nutricional (sistema)</h2>
      {hasDur && (
        <p style={{ fontSize: 14, marginTop: 0 }}>
          <strong>Duración total:</strong> {pdays} días (ciclo base en el plan: 7 días).
        </p>
      )}
      {neObj && (
        <ul style={{ margin: "8px 0", paddingLeft: 20, fontSize: 14 }}>
          {neObj.engine_schema_version != null && (
            <li>Esquema: {String(neObj.engine_schema_version)}</li>
          )}
          {neObj.bmr_kcal != null && <li>TMB estimada: {String(neObj.bmr_kcal)} kcal/día</li>}
          {neObj.tdee_kcal != null && <li>GET (TDEE): {String(neObj.tdee_kcal)} kcal/día</li>}
          {neObj.activity_factor != null && (
            <li>Factor actividad: {String(neObj.activity_factor)}</li>
          )}
          {neObj.bmi != null && <li>IMC: {String(neObj.bmi)}</li>}
          {neObj.goal_calories != null && (
            <li>Objetivo calórico: {String(neObj.goal_calories)} kcal/día</li>
          )}
          {neObj.applied_mode != null && String(neObj.applied_mode) !== "auto" && (
            <li>Modo de objetivos: {String(neObj.applied_mode)}</li>
          )}
          {neObj.manual_override_used === true && (
            <li>Ajuste manual del profesional aplicado</li>
          )}
        </ul>
      )}
      {hasMg && (
        <p style={{ fontSize: 14, margin: "8px 0" }}>
          <strong>Gramos orientativos/día:</strong>{" "}
          {[
            (macroGrams as Record<string, unknown>).protein_g != null &&
              `proteína ~${String((macroGrams as Record<string, unknown>).protein_g)} g`,
            (macroGrams as Record<string, unknown>).carbs_g != null &&
              `hidratos ~${String((macroGrams as Record<string, unknown>).carbs_g)} g`,
            (macroGrams as Record<string, unknown>).fat_g != null &&
              `grasas ~${String((macroGrams as Record<string, unknown>).fat_g)} g`,
          ]
            .filter(Boolean)
            .join(" · ")}
        </p>
      )}
      {hasRules && (
        <p style={{ fontSize: 14, margin: "8px 0" }}>
          <strong>Reglas clínicas aplicadas:</strong> {(rules as string[]).join(", ")}
        </p>
      )}
      {hasAlerts && (
        <div style={{ marginTop: 12 }}>
          <strong style={{ fontSize: 14 }}>Avisos del sistema</strong>
          <ul style={{ fontSize: 13, margin: "6px 0 0", paddingLeft: 20, color: "#5c4033" }}>
            {(alerts as { severity?: string; message_es?: string }[]).map((a, i) => (
              <li key={i}>
                [{String(a.severity || "info").toUpperCase()}]{" "}
                {a.message_es || JSON.stringify(a)}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}

function MealStructurePanel({ plan }: { plan: unknown }) {
  const slots = resolveMealSlots(plan)
  if (!slots.length) return null
  return (
    <div
      style={{
        marginBottom: 24,
        padding: 16,
        background: "#f8fbf4",
        border: "1px solid #d8e4cb",
        borderRadius: 8,
      }}
    >
      <h2 style={{ fontSize: 16, marginTop: 0 }}>Estructura de comidas</h2>
      <p style={{ margin: 0, fontSize: 14 }}>
        <strong>Comidas por día:</strong> {slots.length}
      </p>
      <p style={{ margin: "6px 0 0", fontSize: 14 }}>
        <strong>Estructura diaria:</strong> {mealSlotsSummaryEs(slots)}
      </p>
    </div>
  )
}

export default function DietDetail() {
  const { dietId } = useParams()
  const id = Number(dietId)
  const [diet, setDiet] = useState<Diet | null>(null)
  const [versions, setVersions] = useState<DietVersion[]>([])
  const [error, setError] = useState<string | null>(null)
  const [msg, setMsg] = useState<string | null>(null)
  const [instr, setInstr] = useState("")
  const [regenDuration, setRegenDuration] = useState("7")
  const [mealsPerDay, setMealsPerDay] = useState<MealsPerDay>(4)
  const [strategyMode, setStrategyMode] = useState<DietStrategyMode>("auto")
  const [dietStyle, setDietStyle] = useState("")
  const [macroProtein, setMacroProtein] = useState("")
  const [macroCarbs, setMacroCarbs] = useState("")
  const [macroFat, setMacroFat] = useState("")
  const [manualKcal, setManualKcal] = useState("")
  const [manualProteinG, setManualProteinG] = useState("")
  const [manualCarbsG, setManualCarbsG] = useState("")
  const [manualFatG, setManualFatG] = useState("")
  const [durationPresets, setDurationPresets] = useState<number[]>(() => [
    ...FALLBACK_PLAN_DURATION_PRESETS,
  ])

  useEffect(() => {
    getPlanDurationPresets()
      .then(setDurationPresets)
      .catch(() => {})
  }, [])

  const refresh = useCallback(async () => {
    if (!Number.isFinite(id)) return
    setError(null)
    const [d, v] = await Promise.all([getDiet(id), getDietVersions(id)])
    setDiet(d)
    setVersions(v)
    const plan = d?.structured_plan_json
    if (plan && typeof plan === "object") {
      const pd = planDurationDaysFromPlanJson(plan as Record<string, unknown>)
      if (pd != null) setRegenDuration(String(pd))
      const mpd = (plan as Record<string, unknown>).meals_per_day
      if (typeof mpd === "number" && mpd >= 2 && mpd <= 5) {
        setMealsPerDay(mpd as MealsPerDay)
      }
    }
  }, [id])

  useEffect(() => {
    refresh().catch((e) => setError(e instanceof Error ? e.message : "Error"))
  }, [refresh])

  async function onExport(fmt: "txt" | "json") {
    if (!Number.isFinite(id)) return
    setError(null)
    try {
      await downloadDietExport(id, fmt)
      setMsg(`Downloaded ${fmt.toUpperCase()}`)
    } catch (e) {
      setError(e instanceof Error ? e.message : "Export failed")
    }
  }

  async function onPdf() {
    if (!Number.isFinite(id)) return
    setError(null)
    try {
      await downloadDietPdf(id)
      setMsg("Downloaded PDF")
    } catch (e) {
      setError(e instanceof Error ? e.message : "PDF failed")
    }
  }

  async function onRegenerate(e: FormEvent) {
    e.preventDefault()
    if (!Number.isFinite(id)) return
    setMsg(null)
    setError(null)
    try {
      const clamped = clampDurationDays(regenDuration)
      const strategy = buildDietStrategyBody({
        mealsPerDay,
        strategyMode,
        dietStyle,
        macroProtein,
        macroCarbs,
        macroFat,
        manualKcal,
        manualProteinG,
        manualCarbsG,
        manualFatG,
      })
      const d = await regenerateDiet(id, {
        doctor_instruction: instr.trim() || null,
        duration_days: clamped,
        ...strategy,
      })
      setDiet(d)
      setInstr("")
      const hint = durationAdjustHint(regenDuration)
      setMsg(hint ? `${hint} New version saved.` : "New version saved.")
      const v = await getDietVersions(id)
      setVersions(v)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Regenerate failed")
    }
  }

  if (!Number.isFinite(id)) {
    return <p>Invalid diet</p>
  }

  if (error && !diet) {
    return (
      <div>
        <p>
          <Link to="/diets">← Diets</Link>
        </p>
        <p style={{ color: "#b00020" }}>{error}</p>
      </div>
    )
  }

  if (!diet) {
    return <p>Loading…</p>
  }

  const jsonStr = JSON.stringify(diet.structured_plan_json, null, 2)
  const regenDurationAdjustHint = durationAdjustHint(regenDuration)

  return (
    <div style={{ maxWidth: 900 }}>
      <p>
        <Link to="/diets">← Diets</Link>
        {" · "}
        <Link to={`/patients/${diet.patient_id}`}>Patient #{diet.patient_id}</Link>
      </p>
           <h1 style={{ marginTop: 0 }}>{diet.title || `Diet #${diet.id}`}</h1>
      <p style={{ color: "#666" }}>
        Status: {diet.status} · Updated {diet.updated_at}
      </p>
      <p style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
        <button type="button" onClick={() => onExport("txt")}>
          Download .txt
        </button>
        <button type="button" onClick={() => onExport("json")}>
          Download .json
        </button>
        <button type="button" onClick={() => onPdf()}>
          Download PDF
        </button>
      </p>
      {msg && <p style={{ color: "#0a0" }}>{msg}</p>}
      {error && <p style={{ color: "#b00020" }}>{error}</p>}

      {diet.summary && (
        <div style={{ marginBottom: 24, lineHeight: 1.5 }}>
          <h2 style={{ fontSize: 16 }}>Summary</h2>
          <p style={{ whiteSpace: "pre-wrap" }}>{diet.summary}</p>
        </div>
      )}

      <NutritionEnginePanel plan={diet.structured_plan_json} />
      <MealStructurePanel plan={diet.structured_plan_json} />

      <form
        onSubmit={onRegenerate}
        style={{
          border: "1px solid #ddd",
          borderRadius: 8,
          padding: 16,
          marginBottom: 24,
        }}
      >
        <h2 style={{ fontSize: 16, marginTop: 0 }}>Regenerate (new version)</h2>
        <label style={{ fontSize: 13 }}>Total duration (days, multiple of 7; optional)</label>
        <DurationPresetButtons
          presets={durationPresets}
          onSelect={(d) => setRegenDuration(String(d))}
        />
        <input
          type="number"
          min={7}
          step={7}
          value={regenDuration}
          onChange={(e) => setRegenDuration(e.target.value)}
          style={{ width: "100%", padding: 8, boxSizing: "border-box", marginBottom: 4 }}
        />
        {regenDurationAdjustHint && (
          <p style={{ fontSize: 12, color: "#666", margin: "0 0 8px" }}>
            {regenDurationAdjustHint}
          </p>
        )}
        <label style={{ fontSize: 13, display: "block", marginBottom: 4 }}>
          Comidas por día
        </label>
        <select
          value={String(mealsPerDay)}
          onChange={(e) => setMealsPerDay(Number(e.target.value) as MealsPerDay)}
          style={{ width: "100%", padding: 8, marginBottom: 8, boxSizing: "border-box" }}
        >
          <option value="2">2 comidas: desayuno + cena</option>
          <option value="3">3 comidas: desayuno + almuerzo + cena</option>
          <option value="4">4 comidas: desayuno + almuerzo + merienda + cena</option>
          <option value="5">5 comidas: desayuno + media mañana + almuerzo + merienda + cena</option>
        </select>
        <label style={{ fontSize: 13, display: "block", marginBottom: 4 }}>
          Modo de objetivos nutricionales
        </label>
        <select
          value={strategyMode}
          onChange={(e) => setStrategyMode(e.target.value as DietStrategyMode)}
          style={{ width: "100%", padding: 8, marginBottom: 8, boxSizing: "border-box" }}
        >
          <option value="auto">Automático (motor actual)</option>
          <option value="guided">Guiado (estilo y preferencias de macros)</option>
          <option value="manual">Manual (calorías / macros; advertencias si aplica)</option>
        </select>
        {(strategyMode === "guided" || strategyMode === "manual") && (
          <p style={{ fontSize: 12, color: "#666", margin: "0 0 8px" }}>
            {strategyMode === "manual"
              ? "Modo manual: el sistema puede emitir advertencias clínicas sin bloquear la generación."
              : "Modo guiado: ajusta el reparto respecto al cálculo base del motor según estilo y preferencias."}
          </p>
        )}
        {(strategyMode === "guided" || strategyMode === "manual") && (
          <>
            <label style={{ fontSize: 13 }}>Estilo de dieta (opcional)</label>
            <select
              value={dietStyle}
              onChange={(e) => setDietStyle(e.target.value)}
              style={{ width: "100%", padding: 8, marginBottom: 8, boxSizing: "border-box" }}
            >
              <option value="">— Sin estilo específico —</option>
              <option value="balanced">Equilibrada</option>
              <option value="low_carb">Baja en carbohidratos</option>
              <option value="high_carb">Alta en carbohidratos</option>
              <option value="high_protein">Alta en proteína</option>
              <option value="mediterranean">Mediterránea (orientación)</option>
            </select>
          </>
        )}
        {strategyMode === "guided" && (
          <>
            <label style={{ fontSize: 13 }}>Preferencia proteína</label>
            <select
              value={macroProtein}
              onChange={(e) => setMacroProtein(e.target.value)}
              style={{ width: "100%", padding: 8, marginBottom: 8, boxSizing: "border-box" }}
            >
              <option value="">— Normal —</option>
              <option value="low">Baja</option>
              <option value="normal">Normal</option>
              <option value="high">Alta</option>
            </select>
            <label style={{ fontSize: 13 }}>Preferencia carbohidratos</label>
            <select
              value={macroCarbs}
              onChange={(e) => setMacroCarbs(e.target.value)}
              style={{ width: "100%", padding: 8, marginBottom: 8, boxSizing: "border-box" }}
            >
              <option value="">— Normal —</option>
              <option value="low">Baja</option>
              <option value="normal">Normal</option>
              <option value="high">Alta</option>
            </select>
            <label style={{ fontSize: 13 }}>Preferencia grasas</label>
            <select
              value={macroFat}
              onChange={(e) => setMacroFat(e.target.value)}
              style={{ width: "100%", padding: 8, marginBottom: 8, boxSizing: "border-box" }}
            >
              <option value="">— Normal —</option>
              <option value="low">Baja</option>
              <option value="normal">Normal</option>
              <option value="high">Alta</option>
            </select>
          </>
        )}
        {strategyMode === "manual" && (
          <>
            <label style={{ fontSize: 13 }}>Calorías / día (opcional)</label>
            <input
              type="number"
              min={1}
              step={1}
              value={manualKcal}
              onChange={(e) => setManualKcal(e.target.value)}
              placeholder="ej. 1800"
              style={{ width: "100%", padding: 8, marginBottom: 8, boxSizing: "border-box" }}
            />
            <label style={{ fontSize: 13 }}>Proteína (g/día, opcional)</label>
            <input
              type="number"
              min={1}
              step={0.1}
              value={manualProteinG}
              onChange={(e) => setManualProteinG(e.target.value)}
              style={{ width: "100%", padding: 8, marginBottom: 8, boxSizing: "border-box" }}
            />
            <label style={{ fontSize: 13 }}>Carbohidratos (g/día, opcional)</label>
            <input
              type="number"
              min={1}
              step={0.1}
              value={manualCarbsG}
              onChange={(e) => setManualCarbsG(e.target.value)}
              style={{ width: "100%", padding: 8, marginBottom: 8, boxSizing: "border-box" }}
            />
            <label style={{ fontSize: 13 }}>Grasas (g/día, opcional)</label>
            <input
              type="number"
              min={1}
              step={0.1}
              value={manualFatG}
              onChange={(e) => setManualFatG(e.target.value)}
              style={{ width: "100%", padding: 8, marginBottom: 8, boxSizing: "border-box" }}
            />
          </>
        )}
        <textarea
          value={instr}
          onChange={(e) => setInstr(e.target.value)}
          rows={3}
          placeholder="Optional new instructions for the model"
          style={{ width: "100%", padding: 8, boxSizing: "border-box", marginBottom: 8 }}
        />
        <button type="submit">Regenerate</button>
      </form>

      <h2 style={{ fontSize: 16 }}>Versions</h2>
      <ul style={{ fontSize: 14 }}>
        {versions.map((v) => (
          <li key={v.id}>
            v{v.version_number} · {v.created_at}
            {v.doctor_instruction ? ` · “${v.doctor_instruction.slice(0, 40)}…”` : ""}
          </li>
        ))}
      </ul>

      <h2 style={{ fontSize: 16 }}>Structured plan (JSON)</h2>
      <pre
        style={{
          background: "#f6f6f6",
          padding: 12,
          borderRadius: 8,
          overflow: "auto",
          fontSize: 12,
          maxHeight: 480,
        }}
      >
        {jsonStr}
      </pre>
    </div>
  )
}
