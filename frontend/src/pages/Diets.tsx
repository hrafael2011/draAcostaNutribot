import { FormEvent, useCallback, useEffect, useState } from "react"
import { Link, useNavigate, useSearchParams } from "react-router-dom"
import { BowlFood, MagnifyingGlass, Plus, X, Spinner } from "@phosphor-icons/react"
import GenerationOverlay from "../components/ui/GenerationOverlay"
import { generateDiet, getDiets, getPatients, getPlanDurationPresets } from "../services/api"
import type { Diet, PaginatedDiets } from "../types"
import type { DietStrategyMode, MealsPerDay } from "../types"
import { DurationPresetButtons } from "../components/DurationPresetButtons"
import { Badge } from "../components/ui/Badge"
import { Avatar } from "../components/ui/Avatar"
import { SkeletonRow } from "../components/ui/Skeleton"
import { EmptyState } from "../components/ui/EmptyState"
import { usePatientSearch } from "../hooks/usePatientSearch"
import {
  clampDurationDays,
  durationAdjustHint,
  FALLBACK_PLAN_DURATION_PRESETS,
} from "../utils/duration"
import { buildDietStrategyBody } from "../utils/dietStrategyBody"

const NEXT_FEATURES = { batchDiets: false, advancedStrategies: false }

function extractKcal(diet: Diet): string {
  try {
    const plan = diet.structured_plan_json as Record<string, unknown>
    const nutrition = plan.nutrition_summary as Record<string, unknown> | undefined
    if (nutrition?.daily_calories) return `${nutrition.daily_calories} kcal`
  } catch {
    /* ignore */
  }
  return "—"
}

function relativeDate(dateStr: string): string {
  const now = new Date()
  const date = new Date(dateStr)
  const diffMs = now.getTime() - date.getTime()
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))
  if (diffDays < 0) return "Hoy"
  if (diffDays === 0) return "Hoy"
  if (diffDays === 1) return "Ayer"
  if (diffDays < 7) return `Hace ${diffDays} días`
  if (diffDays < 30) return `Hace ${Math.floor(diffDays / 7)} semanas`
  if (diffDays < 365) return `Hace ${Math.floor(diffDays / 30)} meses`
  return `Hace ${Math.floor(diffDays / 365)} años`
}

const STATUS_CONFIG: Record<
  string,
  { variant: "success" | "warning" | "danger" | "neutral" | "info"; label: string }
> = {
  generated: { variant: "success", label: "Activa" },
  pending_approval: { variant: "warning", label: "Pendiente" },
  discarded: { variant: "neutral", label: "Descartada" },
  draft: { variant: "info", label: "Borrador" },
}

export default function Diets() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const patientFromUrl = searchParams.get("patient")

  /* ---------- data state ---------- */
  const [data, setData] = useState<PaginatedDiets | null>(null)
  const [page, setPage] = useState(1)
  const [error, setError] = useState<string | null>(null)

  /* ---------- patient filter ---------- */
  const [patientIdFilter, setPatientIdFilter] = useState<number | undefined>(
    patientFromUrl ? Number(patientFromUrl) : undefined,
  )
  const [selectedPatientName, setSelectedPatientName] = useState<string | null>(null)

  /* ---------- patient name map (table display) ---------- */
  const [patientNameMap, setPatientNameMap] = useState<
    Record<number, { firstName: string; lastName: string; city?: string | null }>
  >({})

  /* ---------- form state ---------- */
  const [formOpen, setFormOpen] = useState(false)
  const [genPatientId, setGenPatientId] = useState<number | null>(
    patientFromUrl ? Number(patientFromUrl) : null,
  )
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
  const [generating, setGenerating] = useState(false)
  const [generatingFor, setGeneratingFor] = useState("")
  const [durationPresets, setDurationPresets] = useState<number[]>(() => [
    ...FALLBACK_PLAN_DURATION_PRESETS,
  ])

  /* ---------- patient search hooks ---------- */
  const {
    query: filterQuery,
    setQuery: setFilterQuery,
    results: filterResults,
    loading: filterLoading,
  } = usePatientSearch()
  const {
    query: formQuery,
    setQuery: setFormQuery,
    results: formResults,
    loading: formLoading,
  } = usePatientSearch()

  /* ---------- effects ---------- */
  useEffect(() => {
    const p = searchParams.get("patient")
    if (p) {
      const pid = Number(p)
      setPatientIdFilter(pid)
      setGenPatientId(pid)
    }
  }, [searchParams])

  useEffect(() => {
    getPlanDurationPresets()
      .then(setDurationPresets)
      .catch(() => {})
  }, [])

  useEffect(() => {
    getPatients({ page: 1, page_size: 100 })
      .then((res) => {
        const map: Record<number, { firstName: string; lastName: string; city?: string | null }> = {}
        for (const p of res.items) {
          map[p.id] = { firstName: p.first_name, lastName: p.last_name, city: p.city }
        }
        setPatientNameMap(map)
      })
      .catch(() => {})
  }, [])

  const load = useCallback(() => {
    setError(null)
    return getDiets({
      patient_id: patientIdFilter,
      page,
      page_size: 20,
    })
      .then(setData)
      .catch((e: unknown) => setError(e instanceof Error ? e.message : "Error"))
  }, [page, patientIdFilter])

  useEffect(() => {
    load()
  }, [load])

  /* ---------- handlers ---------- */
  function handleFilterSelect(patientId: number, firstName: string, lastName: string) {
    setPatientIdFilter(patientId)
    setGenPatientId(patientId)
    setSelectedPatientName(`${firstName} ${lastName}`)
    setFilterQuery("")
    setPage(1)
  }

  function clearFilter() {
    setPatientIdFilter(undefined)
    setGenPatientId(null)
    setSelectedPatientName(null)
    setFilterQuery("")
    setPage(1)
  }

  function handleFormSelect(patientId: number, firstName: string, lastName: string) {
    setPatientIdFilter(patientId)
    setGenPatientId(patientId)
    setSelectedPatientName(`${firstName} ${lastName}`)
    setFormQuery("")
    setPage(1)
  }

  async function onGenerate(e: FormEvent) {
    e.preventDefault()
    if (!genPatientId) {
      setError("Selecciona un paciente primero")
      return
    }
    setError(null)
    setGenMsg(null)
    setGeneratingFor(selectedPatientName || "Paciente")
    setGenerating(true)
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
        patient_id: genPatientId,
        doctor_instruction: genInstr.trim() || null,
        duration_days: clamped,
        ...strategy,
      })
      navigate(`/diets/${d.id}`)
    } catch (err) {
      setGenerating(false)
      setError(err instanceof Error ? err.message : "Error al generar")
    }
  }

  const genDurationAdjustHint = durationAdjustHint(genDuration)

  /* ---------- helpers ---------- */
  function renderStatusBadge(status: string) {
    const cfg = STATUS_CONFIG[status] ?? { variant: "neutral" as const, label: status }
    return <Badge variant={cfg.variant}>{cfg.label}</Badge>
  }

  function getPatientName(diet: Diet): { firstName: string; lastName: string } | null {
    const p = patientNameMap[diet.patient_id]
    if (p) return { firstName: p.firstName, lastName: p.lastName }
    return null
  }

  const hasBatch = NEXT_FEATURES.batchDiets

  /* ========== render ========== */
  return (
    <div className="mx-auto max-w-5xl px-4 py-8">
      {/* header */}
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-900">Dietas</h1>
        <button
          type="button"
          onClick={() => setFormOpen(!formOpen)}
          className="inline-flex items-center gap-2 rounded-lg bg-emerald-600 px-4 py-2 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-emerald-500"
        >
          <Plus size={18} weight="bold" />
          {formOpen ? "Cerrar" : "Nueva Dieta"}
        </button>
      </div>

      {/* collapsible generation form */}
      {formOpen && (
        <form
          onSubmit={onGenerate}
          className="mb-8 rounded-xl border border-slate-200 bg-white p-6 shadow-sm"
        >
          {/* patient search */}
          <div className="mb-4">
            <label className="mb-1.5 block text-sm font-medium text-slate-700">Paciente</label>
            <div className="relative">
              <MagnifyingGlass
                size={16}
                className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"
              />
              <input
                type="text"
                value={formQuery}
                onChange={(e) => setFormQuery(e.target.value)}
                placeholder="Buscar paciente por nombre..."
                className="w-full rounded-lg border border-slate-300 py-2 pl-10 pr-3 text-sm placeholder-slate-400 focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
              />
              {formLoading && (
                <Spinner
                  size={16}
                  className="absolute right-3 top-1/2 -translate-y-1/2 animate-spin text-slate-400"
                />
              )}
            </div>
            {formResults.length > 0 && (
              <ul className="mt-1 max-h-48 overflow-y-auto rounded-lg border border-slate-200 bg-white shadow-lg">
                {formResults.map((p) => (
                  <li key={p.id}>
                    <button
                      type="button"
                      onClick={() => handleFormSelect(p.id, p.first_name, p.last_name)}
                      className="flex w-full items-center gap-3 px-3 py-2 text-left text-sm hover:bg-slate-50"
                    >
                      <Avatar firstName={p.first_name} lastName={p.last_name} size="sm" />
                      <div>
                        <span className="font-medium text-slate-900">
                          {p.first_name} {p.last_name}
                        </span>
                        {p.city && <span className="ml-2 text-xs text-slate-500">{p.city}</span>}
                      </div>
                    </button>
                  </li>
                ))}
              </ul>
            )}
            {genPatientId != null && selectedPatientName && (
              <div className="mt-2 flex items-center gap-2">
                <span className="inline-flex items-center gap-2 rounded-full bg-emerald-50 px-3 py-1 text-sm text-emerald-700">
                  {selectedPatientName}
                  <button
                    type="button"
                    onClick={() => {
                      setGenPatientId(null)
                      setSelectedPatientName(null)
                    }}
                  >
                    <X size={14} className="text-emerald-500 hover:text-emerald-700" />
                  </button>
                </span>
              </div>
            )}
          </div>

          {/* duration */}
          <div className="mb-4">
            <label className="mb-1.5 block text-sm font-medium text-slate-700">
              Duraci&oacute;n (d&iacute;as, m&uacute;ltiplo de 7)
            </label>
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
              className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
            />
            {genDurationAdjustHint && (
              <p className="mt-1 text-xs text-slate-500">{genDurationAdjustHint}</p>
            )}
          </div>

          {/* meals per day */}
          <div className="mb-4">
            <label className="mb-1.5 block text-sm font-medium text-slate-700">
              Comidas por d&iacute;a
            </label>
            <select
              value={String(mealsPerDay)}
              onChange={(e) => setMealsPerDay(Number(e.target.value) as MealsPerDay)}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
            >
              <option value="2">2 comidas: desayuno + cena</option>
              <option value="3">3 comidas: desayuno + almuerzo + cena</option>
              <option value="4">4 comidas: desayuno + almuerzo + merienda + cena</option>
              <option value="5">
                5 comidas: desayuno + media ma&ntilde;ana + almuerzo + merienda + cena
              </option>
            </select>
          </div>

          {NEXT_FEATURES.advancedStrategies && (<>
          {/* strategy mode */}
          <div className="mb-4">
            <label className="mb-1.5 block text-sm font-medium text-slate-700">
              Modo de objetivos nutricionales
            </label>
            <select
              value={strategyMode}
              onChange={(e) => setStrategyMode(e.target.value as DietStrategyMode)}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
            >
              <option value="auto">Autom&aacute;tico (motor actual)</option>
              <option value="guided">Guiado (estilo y preferencias de macros)</option>
              <option value="manual">Manual (calor&iacute;as / macros; advertencias si aplica)</option>
            </select>
            {(strategyMode === "guided" || strategyMode === "manual") && (
              <p className="mt-1 text-xs text-slate-500">
                {strategyMode === "manual"
                  ? "Modo manual: el sistema puede emitir advertencias cl&iacute;nicas sin bloquear la generaci&oacute;n."
                  : "Modo guiado: ajusta el reparto respecto al c&aacute;lculo base del motor seg&uacute;n estilo y preferencias."}
              </p>
            )}
          </div>

          {/* diet style (guided / manual) */}
          {(strategyMode === "guided" || strategyMode === "manual") && (
            <div className="mb-4">
              <label className="mb-1.5 block text-sm font-medium text-slate-700">
                Estilo de dieta (opcional)
              </label>
              <select
                value={dietStyle}
                onChange={(e) => setDietStyle(e.target.value)}
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
              >
                <option value="">— Sin estilo espec&iacute;fico —</option>
                <option value="balanced">Equilibrada</option>
                <option value="low_carb">Baja en carbohidratos</option>
                <option value="high_carb">Alta en carbohidratos</option>
                <option value="high_protein">Alta en prote&iacute;na</option>
                <option value="mediterranean">Mediterr&aacute;nea (orientaci&oacute;n)</option>
              </select>
            </div>
          )}

          {/* guided macros */}
          {strategyMode === "guided" && (
            <div className="mb-4 grid grid-cols-3 gap-3">
              <div>
                <label className="mb-1.5 block text-sm font-medium text-slate-700">Prote&iacute;na</label>
                <select
                  value={macroProtein}
                  onChange={(e) => setMacroProtein(e.target.value)}
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
                >
                  <option value="">Normal</option>
                  <option value="low">Baja</option>
                  <option value="normal">Normal</option>
                  <option value="high">Alta</option>
                </select>
              </div>
              <div>
                <label className="mb-1.5 block text-sm font-medium text-slate-700">
                  Carbohidratos
                </label>
                <select
                  value={macroCarbs}
                  onChange={(e) => setMacroCarbs(e.target.value)}
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
                >
                  <option value="">Normal</option>
                  <option value="low">Baja</option>
                  <option value="normal">Normal</option>
                  <option value="high">Alta</option>
                </select>
              </div>
              <div>
                <label className="mb-1.5 block text-sm font-medium text-slate-700">Grasas</label>
                <select
                  value={macroFat}
                  onChange={(e) => setMacroFat(e.target.value)}
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
                >
                  <option value="">Normal</option>
                  <option value="low">Baja</option>
                  <option value="normal">Normal</option>
                  <option value="high">Alta</option>
                </select>
              </div>
            </div>
          )}

          {/* manual targets */}
          {strategyMode === "manual" && (
            <div className="mb-4 grid grid-cols-2 gap-3">
              <div>
                <label className="mb-1.5 block text-sm font-medium text-slate-700">
                  Calor&iacute;as / d&iacute;a (opcional)
                </label>
                <input
                  type="number"
                  min={1}
                  value={manualKcal}
                  onChange={(e) => setManualKcal(e.target.value)}
                  placeholder="ej. 1800"
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm placeholder-slate-400 focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
                />
              </div>
              <div>
                <label className="mb-1.5 block text-sm font-medium text-slate-700">
                  Prote&iacute;na (g/d&iacute;a, opcional)
                </label>
                <input
                  type="number"
                  min={1}
                  step={0.1}
                  value={manualProteinG}
                  onChange={(e) => setManualProteinG(e.target.value)}
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
                />
              </div>
              <div>
                <label className="mb-1.5 block text-sm font-medium text-slate-700">
                  Carbohidratos (g/d&iacute;a, opcional)
                </label>
                <input
                  type="number"
                  min={1}
                  step={0.1}
                  value={manualCarbsG}
                  onChange={(e) => setManualCarbsG(e.target.value)}
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
                />
              </div>
              <div>
                <label className="mb-1.5 block text-sm font-medium text-slate-700">
                  Grasas (g/d&iacute;a, opcional)
                </label>
                <input
                  type="number"
                  min={1}
                  step={0.1}
                  value={manualFatG}
                  onChange={(e) => setManualFatG(e.target.value)}
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
                />
              </div>
            </div>
          )}
          </>)}

          {/* instructions */}
          <div className="mb-4">
            <label className="mb-1.5 block text-sm font-medium text-slate-700">
              Instructions for the model (optional)
            </label>
            <textarea
              value={genInstr}
              onChange={(e) => setGenInstr(e.target.value)}
              rows={3}
              placeholder="e.g. avoid dairy, budget-friendly"
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm placeholder-slate-400 focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
            />
          </div>

          <button
            type="submit"
            className="inline-flex items-center gap-2 rounded-lg bg-emerald-600 px-5 py-2.5 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-emerald-500"
          >
            Generar Dieta
          </button>
        </form>
      )}

      {/* status messages */}
      {genMsg && (
        <div className="mb-4 rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700">
          {genMsg}
        </div>
      )}
      {error && (
        <div className="mb-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {/* filter bar */}
      <div className="mb-6 flex flex-wrap items-center gap-3">
        <div className="relative min-w-[240px] flex-1">
          <MagnifyingGlass
            size={16}
            className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"
          />
          <input
            type="text"
            value={filterQuery}
            onChange={(e) => setFilterQuery(e.target.value)}
            placeholder="Filtrar por paciente..."
            className="w-full rounded-lg border border-slate-300 py-2 pl-10 pr-3 text-sm placeholder-slate-400 focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
          />
          {filterLoading && (
            <Spinner
              size={16}
              className="absolute right-3 top-1/2 -translate-y-1/2 animate-spin text-slate-400"
            />
          )}
        </div>
        <button
          type="button"
          onClick={() => load()}
          className="inline-flex items-center gap-2 rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-600 transition-colors hover:bg-slate-50"
        >
          Actualizar
        </button>
      </div>

      {/* search results dropdown */}
      {filterResults.length > 0 && (
        <div className="mb-4 rounded-lg border border-slate-200 bg-white shadow-lg">
          <ul className="divide-y divide-slate-100">
            {filterResults.map((p) => (
              <li key={p.id}>
                <button
                  type="button"
                  onClick={() => handleFilterSelect(p.id, p.first_name, p.last_name)}
                  className="flex w-full items-center gap-3 px-4 py-3 text-left text-sm transition-colors hover:bg-slate-50"
                >
                  <Avatar firstName={p.first_name} lastName={p.last_name} size="sm" />
                  <div className="flex-1">
                    <span className="font-medium text-slate-900">
                      {p.first_name} {p.last_name}
                    </span>
                    {p.city && <span className="ml-2 text-xs text-slate-500">{p.city}</span>}
                  </div>
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* active filter chip */}
      {patientIdFilter != null && selectedPatientName && (
        <div className="mb-4 flex items-center gap-2">
          <span className="inline-flex items-center gap-2 rounded-full bg-emerald-50 px-3 py-1.5 text-sm text-emerald-700 ring-1 ring-emerald-600/20">
            {selectedPatientName}
            <button
              type="button"
              onClick={clearFilter}
              className="text-emerald-500 hover:text-emerald-700"
            >
              <X size={14} />
            </button>
          </span>
          <span className="text-xs text-slate-400">
            {data ? `${data.total} dietas encontradas` : ""}
          </span>
        </div>
      )}

      {/* loading state */}
      {!data ? (
        <div className="divide-y divide-slate-100 rounded-xl border border-slate-200 bg-white">
          {Array.from({ length: 5 }).map((_, i) => (
            <SkeletonRow key={i} />
          ))}
        </div>
      ) : data.items.length === 0 ? (
        <EmptyState
          icon={<BowlFood size={48} weight="thin" />}
          title="Sin dietas"
          description={
            patientIdFilter != null
              ? "Este paciente no tiene dietas generadas a&uacute;n."
              : "No hay dietas generadas a&uacute;n. Crea una nueva usando el formulario."
          }
          action={
            !formOpen ? (
              <button
                type="button"
                onClick={() => setFormOpen(true)}
                className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-emerald-500"
              >
                Nueva Dieta
              </button>
            ) : undefined
          }
        />
      ) : (
        <>
          {/* table */}
          <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white shadow-sm">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-slate-200 bg-slate-50">
                  {hasBatch && (
                    <th className="w-10 px-4 py-3">
                      <input type="checkbox" className="rounded" />
                    </th>
                  )}
                  <th className="px-4 py-3 font-semibold text-slate-700">Paciente</th>
                  <th className="px-4 py-3 font-semibold text-slate-700">Plan</th>
                  <th className="px-4 py-3 font-semibold text-slate-700">Estado</th>
                  <th className="px-4 py-3 font-semibold text-slate-700">Generada</th>
                  <th className="px-4 py-3 font-semibold text-slate-700">Acciones</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {data.items.map((d: Diet) => {
                  const name = getPatientName(d)
                  return (
                    <tr key={d.id} className="transition-colors hover:bg-slate-50">
                      {hasBatch && (
                        <td className="px-4 py-3">
                          <input type="checkbox" className="rounded" />
                        </td>
                      )}
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-3">
                          {name ? (
                            <Avatar firstName={name.firstName} lastName={name.lastName} size="sm" />
                          ) : (
                            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-slate-100 text-xs font-semibold text-slate-500">
                              ?
                            </div>
                          )}
                          <span className="font-medium text-slate-900">
                            {name
                              ? `${name.firstName} ${name.lastName}`
                              : `Paciente #${d.patient_id}`}
                          </span>
                        </div>
                      </td>
                      <td className="px-4 py-3 text-slate-600">{extractKcal(d)}</td>
                      <td className="px-4 py-3">{renderStatusBadge(d.status)}</td>
                      <td className="px-4 py-3 text-xs text-slate-500">{relativeDate(d.created_at)}</td>
                      <td className="px-4 py-3">
                        <Link
                          to={`/diets/${d.id}`}
                          className="font-medium text-emerald-600 transition-colors hover:text-emerald-500"
                        >
                          Ver &rarr;
                        </Link>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>

          {/* pagination */}
          <div className="mt-4 flex items-center justify-between">
            <span className="text-sm text-slate-500">
              P&aacute;gina {page} &middot; {data.total} total
            </span>
            <div className="flex items-center gap-2">
              <button
                type="button"
                disabled={page <= 1}
                onClick={() => setPage((p) => p - 1)}
                className="rounded-lg border border-slate-300 px-3 py-1.5 text-sm font-medium text-slate-600 transition-colors hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40"
              >
                Anterior
              </button>
              <button
                type="button"
                disabled={page * data.page_size >= data.total}
                onClick={() => setPage((p) => p + 1)}
                className="rounded-lg border border-slate-300 px-3 py-1.5 text-sm font-medium text-slate-600 transition-colors hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40"
              >
                Siguiente
              </button>
            </div>
          </div>
        </>
      )}
      <GenerationOverlay
        open={generating}
        patientName={generatingFor}
        onComplete={() => {}}
      />
    </div>
  )
}
