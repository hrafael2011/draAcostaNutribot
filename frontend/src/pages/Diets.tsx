import { FormEvent, useCallback, useEffect, useState } from "react"
import { Link, useSearchParams } from "react-router-dom"
import { generateDiet, getDiets, getPlanDurationPresets } from "../services/api"
import type { Diet, PaginatedDiets } from "../types"
import { DurationPresetButtons } from "../components/DurationPresetButtons"
import {
  clampDurationDays,
  durationAdjustHint,
  FALLBACK_PLAN_DURATION_PRESETS,
  planDurationDaysFromPlanJson,
} from "../utils/duration"
import { buildDietStrategyBody } from "../utils/dietStrategyBody"
import type { DietStrategyMode, MealsPerDay } from "../types"

function dietListDurationLabel(d: Diet): string {
  const days = planDurationDaysFromPlanJson(d.structured_plan_json)
  return days != null ? `${days} d` : "—"
}

export default function Diets() {
  const [searchParams] = useSearchParams()
  const patientFromUrl = searchParams.get("patient")

  const [data, setData] = useState<PaginatedDiets | null>(null)
  const [patientId, setPatientId] = useState(patientFromUrl || "")
  const [page, setPage] = useState(1)
  const [error, setError] = useState<string | null>(null)
  const [genPatient, setGenPatient] = useState(patientFromUrl || "")
  const [genInstr, setGenInstr] = useState("")
  const [genDuration, setGenDuration] = useState("7")
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
  const [genMsg, setGenMsg] = useState<string | null>(null)
  const [durationPresets, setDurationPresets] = useState<number[]>(() => [
    ...FALLBACK_PLAN_DURATION_PRESETS,
  ])

  useEffect(() => {
    const p = searchParams.get("patient")
    if (p) {
      setPatientId(p)
      setGenPatient(p)
    }
  }, [searchParams])

  useEffect(() => {
    getPlanDurationPresets()
      .then(setDurationPresets)
      .catch(() => {})
  }, [])

  const parsedFilter = Number(patientId)
  const pidFilter =
    patientId.trim() === "" || !Number.isFinite(parsedFilter)
      ? undefined
      : parsedFilter

  const load = useCallback(() => {
    setError(null)
    return getDiets({
      patient_id: pidFilter,
      page,
      page_size: 20,
    })
      .then(setData)
      .catch((e) => setError(e instanceof Error ? e.message : "Error"))
  }, [page, pidFilter])

  useEffect(() => {
    load()
  }, [load])

  async function onGenerate(e: FormEvent) {
    e.preventDefault()
    const pid = Number(genPatient)
    if (!Number.isFinite(pid)) {
      setError("Patient ID must be a number")
      return
    }
    setError(null)
    setGenMsg(null)
    try {
      const clamped = clampDurationDays(genDuration)
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
      const d = await generateDiet({
        patient_id: pid,
        doctor_instruction: genInstr.trim() || null,
        duration_days: clamped,
        ...strategy,
      })
      const hint = durationAdjustHint(genDuration)
      setGenMsg(
        hint ? `${hint} Created diet #${d.id}.` : `Created diet #${d.id}`
      )
      setGenInstr("")
      await load()
    } catch (err) {
      setError(err instanceof Error ? err.message : "Generation failed")
    }
  }

  const genDurationAdjustHint = durationAdjustHint(genDuration)

  return (
    <div>
      <h1 style={{ marginTop: 0 }}>Diets</h1>
      <p style={{ color: "#555", maxWidth: 720 }}>
        Generate a 7-day cycle plan with AI (total duration in days must be a multiple of 7). Requires complete
        patient profile, latest weight and height, and <code>OPENAI_API_KEY</code> on the server. Each run creates a
        new diet record; use the detail page to regenerate a new version.
      </p>

      <form
        onSubmit={onGenerate}
        style={{
          border: "1px solid #ddd",
          borderRadius: 8,
          padding: 16,
          marginBottom: 24,
          maxWidth: 520,
        }}
      >
        <h2 style={{ fontSize: 16, marginTop: 0 }}>Generate new diet</h2>
        <label style={{ fontSize: 13 }}>Patient ID</label>
        <input
          required
          type="number"
          value={genPatient}
          onChange={(e) => setGenPatient(e.target.value)}
          style={{ width: "100%", padding: 8, marginBottom: 8, boxSizing: "border-box" }}
        />
        <label style={{ fontSize: 13 }}>Total duration (days, multiple of 7)</label>
        <DurationPresetButtons
          presets={durationPresets}
          onSelect={(d) => setGenDuration(String(d))}
        />
        <input
          type="number"
          min={7}
          step={7}
          value={genDuration}
          onChange={(e) => setGenDuration(e.target.value)}
          style={{ width: "100%", padding: 8, marginBottom: 4, boxSizing: "border-box" }}
        />
        {genDurationAdjustHint && (
          <p style={{ fontSize: 12, color: "#666", margin: "0 0 8px" }}>
            {genDurationAdjustHint}
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
        <label style={{ fontSize: 13 }}>Instructions for the model (optional)</label>
        <textarea
          value={genInstr}
          onChange={(e) => setGenInstr(e.target.value)}
          rows={3}
          placeholder="e.g. avoid dairy, budget-friendly"
          style={{ width: "100%", padding: 8, marginBottom: 8, boxSizing: "border-box" }}
        />
        <button type="submit">Generate</button>
      </form>

      {genMsg && <p style={{ color: "#0a0" }}>{genMsg}</p>}
      {error && <p style={{ color: "#b00020" }}>{error}</p>}

      <div style={{ marginBottom: 16, display: "flex", gap: 8, flexWrap: "wrap", alignItems: "center" }}>
        <label style={{ fontSize: 14 }}>Filter by patient ID</label>
        <input
          type="number"
          value={patientId}
          onChange={(e) => {
            setPatientId(e.target.value)
            setPage(1)
          }}
          placeholder="all"
          style={{ padding: 8, width: 120 }}
        />
        <button type="button" onClick={() => load()}>
          Refresh
        </button>
      </div>

      {!data ? (
        <p>Loading…</p>
      ) : (
        <>
          <table style={{ borderCollapse: "collapse", width: "100%", maxWidth: 960 }}>
            <thead>
              <tr style={{ textAlign: "left", borderBottom: "1px solid #ccc" }}>
                <th style={{ padding: 8 }}>ID</th>
                <th style={{ padding: 8 }}>Patient</th>
                <th style={{ padding: 8 }}>Title</th>
                <th style={{ padding: 8 }}>Duration</th>
                <th style={{ padding: 8 }}>Status</th>
                <th style={{ padding: 8 }}>Updated</th>
              </tr>
            </thead>
            <tbody>
              {data.items.map((d: Diet) => (
                <tr key={d.id} style={{ borderBottom: "1px solid #eee" }}>
                  <td style={{ padding: 8 }}>
                    <Link to={`/diets/${d.id}`}>#{d.id}</Link>
                  </td>
                  <td style={{ padding: 8 }}>
                    <Link to={`/patients/${d.patient_id}`}>#{d.patient_id}</Link>
                  </td>
                  <td style={{ padding: 8 }}>{d.title || "—"}</td>
                  <td style={{ padding: 8, fontSize: 13 }}>{dietListDurationLabel(d)}</td>
                  <td style={{ padding: 8 }}>{d.status}</td>
                  <td style={{ padding: 8, fontSize: 13 }}>{d.updated_at}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <div style={{ marginTop: 16, display: "flex", gap: 12, alignItems: "center" }}>
            <button type="button" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
              Previous
            </button>
            <span>
              Page {page} · {data.total} total
            </span>
            <button
              type="button"
              disabled={page * data.page_size >= data.total}
              onClick={() => setPage((p) => p + 1)}
            >
              Next
            </button>
          </div>
        </>
      )}
    </div>
  )
}
