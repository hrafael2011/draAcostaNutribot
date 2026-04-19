import { FormEvent, useCallback, useEffect, useState } from "react"
import { Link, useParams } from "react-router-dom"
import {
  addMetric,
  getMetrics,
  getPatient,
  getPatientSummary,
  getProfile,
  patchPatient,
  patchProfile,
} from "../services/api"
import type { Patient, PatientMetric, PatientProfile, PatientSummary } from "../types"

type Tab = "summary" | "data" | "profile" | "metrics"

const inputStyle = {
  width: "100%",
  padding: 8,
  marginBottom: 8,
  boxSizing: "border-box" as const,
}

const selectStyle = {
  ...inputStyle,
  background: "#fff",
  border: "1px solid #ccc",
  borderRadius: 4,
  height: 36,
}

// ── Opciones predefinidas ───────────────────────────────────────────────────

const DISEASE_OPTIONS = [
  "Diabetes",
  "Hipertensión",
  "Problemas renales",
  "Dislipidemia",
  "Hipotiroidismo",
  "Hernias lumbares",
]

const ALLERGY_OPTIONS = [
  "Gluten",
  "Lactosa",
  "Mariscos",
  "Nueces/frutos secos",
  "Huevo",
  "Soja",
]

const DIETARY_STYLE_OPTIONS = [
  "Omnívoro",
  "Vegetariano",
  "Vegano",
  "Sin gluten",
  "Sin lactosa",
  "Keto",
  "Mediterráneo",
]

const EXERCISE_TYPE_OPTIONS = [
  "Fuerza",
  "Cardio",
  "Fuerza + Cardio",
  "Yoga/Pilates",
  "Natación",
  "Caminata",
  "Deporte de equipo",
]

const FOODS_AVOIDED_OPTIONS = [
  "Carnes rojas",
  "Cerdo",
  "Mariscos",
  "Lácteos",
  "Gluten",
  "Azúcar procesada",
  "Frituras",
]

// ── Helpers multi-selección ─────────────────────────────────────────────────

function parseMultiValue(
  raw: string | null | undefined,
  options: string[]
): [string[], string] {
  if (!raw) return [[], ""]
  const parts = raw
    .split(/,\s*/)
    .map((s) => s.trim())
    .filter(Boolean)
  const known = parts.filter((p) => options.includes(p))
  const other = parts.filter((p) => !options.includes(p)).join(", ")
  return [known, other]
}

function buildMultiValue(pills: string[], otherText: string): string | null {
  const all = [...pills]
  if (otherText.trim()) all.push(otherText.trim())
  return all.length > 0 ? all.join(", ") : null
}

// ── Componente PillSelect ───────────────────────────────────────────────────

interface PillSelectProps {
  options: string[]
  selected: string[]
  otherText: string
  onChange: (selected: string[]) => void
  onOtherChange: (text: string) => void
  hasOther?: boolean
}

function PillSelect({
  options,
  selected,
  otherText,
  onChange,
  onOtherChange,
  hasOther = true,
}: PillSelectProps) {
  const toggle = (opt: string) => {
    if (selected.includes(opt)) {
      onChange(selected.filter((s) => s !== opt))
    } else {
      onChange([...selected, opt])
    }
  }

  const [showOther, setShowOther] = useState(otherText !== "")

  useEffect(() => {
    setShowOther(otherText !== "")
  }, [otherText])

  const toggleOther = () => {
    if (showOther) {
      setShowOther(false)
      onOtherChange("")
    } else {
      setShowOther(true)
    }
  }

  return (
    <div style={{ marginBottom: 8 }}>
      <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
        {options.map((opt) => {
          const active = selected.includes(opt)
          return (
            <button
              key={opt}
              type="button"
              onClick={() => toggle(opt)}
              style={{
                padding: "4px 12px",
                borderRadius: 16,
                border: `1px solid ${active ? "#1e3a5f" : "#ccc"}`,
                background: active ? "#1e3a5f" : "#fff",
                color: active ? "#fff" : "#333",
                cursor: "pointer",
                fontSize: 13,
                fontWeight: active ? 600 : 400,
              }}
            >
              {opt}
            </button>
          )
        })}
        {hasOther && (
          <button
            type="button"
            onClick={toggleOther}
            style={{
              padding: "4px 12px",
              borderRadius: 16,
              border: `1px solid ${showOther ? "#1e3a5f" : "#ccc"}`,
              background: showOther ? "#1e3a5f" : "#fff",
              color: showOther ? "#fff" : "#333",
              cursor: "pointer",
              fontSize: 13,
            }}
          >
            Otro
          </button>
        )}
      </div>
      {hasOther && showOther && (
        <input
          type="text"
          value={otherText}
          onChange={(e) => onOtherChange(e.target.value)}
          placeholder="Especificar..."
          style={{ ...inputStyle, marginTop: 6, width: "100%" }}
        />
      )}
    </div>
  )
}

// ── Componente principal ────────────────────────────────────────────────────

export default function PatientDetail() {
  const { patientId: idParam } = useParams()
  const patientId = Number(idParam)
  const [tab, setTab] = useState<Tab>("summary")
  const [patient, setPatient] = useState<Patient | null>(null)
  const [summary, setSummary] = useState<PatientSummary | null>(null)
  const [profile, setProfile] = useState<PatientProfile | null>(null)
  const [metrics, setMetrics] = useState<PatientMetric[]>([])
  const [error, setError] = useState<string | null>(null)
  const [msg, setMsg] = useState<string | null>(null)

  const [mWeight, setMWeight] = useState("")
  const [mHeight, setMHeight] = useState("")
  const [mNotes, setMNotes] = useState("")

  // ── Estado multi-selección del perfil clínico ───────────────────────────
  const [diseasesPills, setDiseasesPills] = useState<string[]>([])
  const [diseasesOther, setDiseasesOther] = useState("")
  const [allergiesPills, setAllergiesPills] = useState<string[]>([])
  const [allergiesOther, setAllergiesOther] = useState("")
  const [dietaryPills, setDietaryPills] = useState<string[]>([])
  const [dietaryOther, setDietaryOther] = useState("")
  const [exerciseTypePills, setExerciseTypePills] = useState<string[]>([])
  const [exerciseTypeOther, setExerciseTypeOther] = useState("")
  const [foodsAvoidedPills, setFoodsAvoidedPills] = useState<string[]>([])
  const [foodsAvoidedOther, setFoodsAvoidedOther] = useState("")

  // Inicializar pills desde perfil cargado
  useEffect(() => {
    if (!profile) return
    const [dp, do_] = parseMultiValue(profile.diseases, DISEASE_OPTIONS)
    setDiseasesPills(dp)
    setDiseasesOther(do_)
    const [ap, ao] = parseMultiValue(profile.food_allergies, ALLERGY_OPTIONS)
    setAllergiesPills(ap)
    setAllergiesOther(ao)
    const [dsp, dso] = parseMultiValue(profile.dietary_style, DIETARY_STYLE_OPTIONS)
    setDietaryPills(dsp)
    setDietaryOther(dso)
    const [etp, eto] = parseMultiValue(profile.exercise_type, EXERCISE_TYPE_OPTIONS)
    setExerciseTypePills(etp)
    setExerciseTypeOther(eto)
    const [fap, fao] = parseMultiValue(profile.foods_avoided, FOODS_AVOIDED_OPTIONS)
    setFoodsAvoidedPills(fap)
    setFoodsAvoidedOther(fao)
  }, [profile])

  const refreshSummary = useCallback(async () => {
    try {
      const s = await getPatientSummary(patientId)
      setSummary(s)
    } catch {
      setSummary(null)
    }
  }, [patientId])

  const refreshProfile = useCallback(async () => {
    const pr = await getProfile(patientId)
    setProfile(pr)
  }, [patientId])

  const refreshMetrics = useCallback(async () => {
    const m = await getMetrics(patientId)
    setMetrics(m)
  }, [patientId])

  useEffect(() => {
    if (!patientId || Number.isNaN(patientId)) return
    let cancelled = false
    setError(null)
    Promise.all([getPatient(patientId), getProfile(patientId)])
      .then(([p, pr]) => {
        if (cancelled) return
        setPatient(p)
        setProfile(pr)
      })
      .catch((e) => {
        if (!cancelled) setError(e instanceof Error ? e.message : "Error")
      })
    return () => {
      cancelled = true
    }
  }, [patientId])

  useEffect(() => {
    if (!patientId || Number.isNaN(patientId)) return
    if (tab === "summary") refreshSummary().catch(() => setSummary(null))
    if (tab === "metrics") refreshMetrics().catch(() => setMetrics([]))
    if (tab === "profile") refreshProfile().catch(() => setProfile(null))
  }, [tab, patientId, refreshSummary, refreshMetrics, refreshProfile])

  async function onSaveData(e: FormEvent) {
    e.preventDefault()
    if (!patient) return
    setMsg(null)
    setError(null)
    try {
      const form = e.target as HTMLFormElement
      const fd = new FormData(form)
      const body: Record<string, unknown> = {
        first_name: fd.get("first_name") as string,
        last_name: fd.get("last_name") as string,
        birth_date: (fd.get("birth_date") as string) || null,
        sex: (fd.get("sex") as string) || null,
        email: (fd.get("email") as string) || null,
        whatsapp: (fd.get("whatsapp") as string) || null,
        country: (fd.get("country") as string) || null,
        city: (fd.get("city") as string) || null,
        is_active: fd.get("is_active") === "on",
        is_archived: fd.get("is_archived") === "on",
      }
      const p = await patchPatient(patientId, body)
      setPatient(p)
      setMsg("Datos guardados")
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error")
    }
  }

  async function onSaveProfile(e: FormEvent) {
    e.preventDefault()
    setMsg(null)
    setError(null)
    try {
      const form = e.target as HTMLFormElement
      const fd = new FormData(form)
      const num = (k: string) => {
        const v = fd.get(k) as string
        if (!v) return null
        const n = Number(v)
        return Number.isFinite(n) ? n : null
      }
      const body: Record<string, unknown> = {
        objective: (fd.get("objective") as string) || null,
        // Multi-selección: leídos desde estado
        diseases: buildMultiValue(diseasesPills, diseasesOther),
        medications: (fd.get("medications") as string) || null,
        food_allergies: buildMultiValue(allergiesPills, allergiesOther),
        foods_avoided: buildMultiValue(foodsAvoidedPills, foodsAvoidedOther),
        medical_history: (fd.get("medical_history") as string) || null,
        dietary_style: buildMultiValue(dietaryPills, dietaryOther),
        food_preferences: (fd.get("food_preferences") as string) || null,
        disliked_foods: (fd.get("disliked_foods") as string) || null,
        water_intake_liters: num("water_intake_liters"),
        activity_level: (fd.get("activity_level") as string) || null,
        stress_level: num("stress_level"),
        sleep_quality: num("sleep_quality"),
        sleep_hours: num("sleep_hours"),
        budget_level: (fd.get("budget_level") as string) || null,
        adherence_level: num("adherence_level"),
        exercise_frequency_per_week: num("exercise_frequency_per_week"),
        exercise_type: buildMultiValue(exerciseTypePills, exerciseTypeOther),
        extra_notes: (fd.get("extra_notes") as string) || null,
      }
      const pr = await patchProfile(patientId, body)
      setProfile(pr)
      setMsg("Perfil guardado")
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error")
    }
  }

  async function onAddMetric(e: FormEvent) {
    e.preventDefault()
    setMsg(null)
    setError(null)
    try {
      await addMetric(patientId, {
        weight_kg: mWeight ? Number(mWeight) : null,
        height_cm: mHeight ? Number(mHeight) : null,
        notes: mNotes || null,
        source: "admin",
      })
      setMWeight("")
      setMHeight("")
      setMNotes("")
      await refreshMetrics()
      setMsg("Medición registrada")
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error")
    }
  }

  const tabBtn = (t: Tab, label: string) => (
    <button
      type="button"
      onClick={() => {
        setTab(t)
        setMsg(null)
        setError(null)
      }}
      style={{
        padding: "8px 12px",
        border: "1px solid #ccc",
        background: tab === t ? "#111" : "#fff",
        color: tab === t ? "#fff" : "#111",
        cursor: "pointer",
      }}
    >
      {label}
    </button>
  )

  if (!patientId || Number.isNaN(patientId)) {
    return <p>Paciente no válido</p>
  }

  if (!patient) {
    return (
      <div>
        <p>
          <Link to="/patients">← Pacientes</Link>
          {" · "}
          <Link to={`/diets?patient=${patientId}`}>Dietas de este paciente</Link>
        </p>
        {error ? (
          <p style={{ color: "#b00020" }}>{error}</p>
        ) : (
          <p>Cargando…</p>
        )}
      </div>
    )
  }

  return (
    <div>
      <p>
        <Link to="/patients">← Pacientes</Link>
        {" · "}
        <Link to={`/diets?patient=${patientId}`}>Dietas de este paciente</Link>
      </p>
      <h1 style={{ marginTop: 0 }}>
        {patient.first_name} {patient.last_name}
      </h1>
      <div style={{ display: "flex", gap: 8, marginBottom: 16, flexWrap: "wrap" }}>
        {tabBtn("summary", "Resumen")}
        {tabBtn("data", "Datos demográficos")}
        {tabBtn("profile", "Perfil clínico")}
        {tabBtn("metrics", "Métricas")}
      </div>
      {error && <p style={{ color: "#b00020" }}>{error}</p>}
      {msg && <p style={{ color: "#0a0" }}>{msg}</p>}

      {/* ── Resumen ─────────────────────────────────────────────────────── */}
      {tab === "summary" && (
        <div>
          {!summary ? (
            <p>Cargando…</p>
          ) : (
            <div style={{ maxWidth: 560 }}>
              <p>
                <strong>Perfil completo:</strong>{" "}
                {summary.profile_flags.is_profile_complete ? "sí" : "no"}
              </p>
              <p>
                <strong>Alergias registradas:</strong>{" "}
                {summary.profile_flags.has_allergies ? "sí" : "no"}
              </p>
              <p>
                <strong>Enfermedades registradas:</strong>{" "}
                {summary.profile_flags.has_diseases ? "sí" : "no"}
              </p>
              {summary.latest_metrics && (
                <p>
                  <strong>Último peso / talla:</strong>{" "}
                  {summary.latest_metrics.weight_kg ?? "—"} kg ·{" "}
                  {summary.latest_metrics.height_cm ?? "—"} cm
                </p>
              )}
              {summary.latest_diet && (
                <p>
                  <strong>Última dieta:</strong> #{summary.latest_diet.id} ·{" "}
                  {summary.latest_diet.created_at}
                  {summary.latest_diet.plan_duration_days != null &&
                  summary.latest_diet.plan_duration_days > 0
                    ? ` · ${summary.latest_diet.plan_duration_days} días`
                    : ""}
                </p>
              )}
            </div>
          )}
        </div>
      )}

      {/* ── Datos demográficos ──────────────────────────────────────────── */}
      {tab === "data" && (
        <form onSubmit={onSaveData} style={{ maxWidth: 480 }}>
          <label style={{ fontSize: 13 }}>Nombre</label>
          <input name="first_name" defaultValue={patient.first_name} style={inputStyle} required />

          <label style={{ fontSize: 13 }}>Apellido</label>
          <input name="last_name" defaultValue={patient.last_name} style={inputStyle} required />

          <label style={{ fontSize: 13 }}>Fecha de nacimiento</label>
          <input
            name="birth_date"
            type="date"
            defaultValue={patient.birth_date?.slice(0, 10) ?? ""}
            style={inputStyle}
          />

          <label style={{ fontSize: 13 }}>Sexo</label>
          <select name="sex" defaultValue={patient.sex ?? ""} style={selectStyle}>
            <option value="">— Seleccionar —</option>
            <option value="Masculino">Masculino</option>
            <option value="Femenino">Femenino</option>
            <option value="Otro">Otro</option>
          </select>

          <label style={{ fontSize: 13 }}>Correo electrónico</label>
          <input name="email" type="email" defaultValue={patient.email ?? ""} style={inputStyle} />

          <label style={{ fontSize: 13 }}>WhatsApp</label>
          <input name="whatsapp" defaultValue={patient.whatsapp ?? ""} style={inputStyle} />

          <label style={{ fontSize: 13 }}>País</label>
          <input name="country" defaultValue={patient.country ?? ""} style={inputStyle} />

          <label style={{ fontSize: 13 }}>Ciudad</label>
          <input name="city" defaultValue={patient.city ?? ""} style={inputStyle} />

          <label style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 8 }}>
            <input type="checkbox" name="is_active" defaultChecked={patient.is_active} />
            Activo
          </label>
          <label style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 16 }}>
            <input type="checkbox" name="is_archived" defaultChecked={patient.is_archived} />
            Archivado
          </label>
          <button type="submit">Guardar</button>
        </form>
      )}

      {/* ── Perfil clínico ──────────────────────────────────────────────── */}
      {tab === "profile" && (
        <form onSubmit={onSaveProfile} style={{ maxWidth: 680 }}>

          {/* Objetivo */}
          <label style={{ fontSize: 13 }}>Objetivo</label>
          <select name="objective" defaultValue={profile?.objective ?? ""} style={selectStyle}>
            <option value="">— Seleccionar —</option>
            <option value="Bajar de peso">Bajar de peso</option>
            <option value="Mantenimiento">Mantenimiento</option>
            <option value="Ganar músculo">Ganar músculo</option>
            <option value="Subir de peso">Subir de peso</option>
          </select>

          {/* Enfermedades — multi-selección */}
          <label style={{ fontSize: 13, display: "block", marginBottom: 4 }}>Enfermedades</label>
          <PillSelect
            options={DISEASE_OPTIONS}
            selected={diseasesPills}
            otherText={diseasesOther}
            onChange={setDiseasesPills}
            onOtherChange={setDiseasesOther}
          />

          {/* Medicamentos */}
          <label style={{ fontSize: 13 }}>Medicamentos</label>
          <textarea
            name="medications"
            rows={2}
            defaultValue={profile?.medications ?? ""}
            style={{ ...inputStyle, minHeight: 48 }}
          />

          {/* Alergias alimentarias — multi-selección */}
          <label style={{ fontSize: 13, display: "block", marginBottom: 4 }}>Alergias alimentarias</label>
          <PillSelect
            options={ALLERGY_OPTIONS}
            selected={allergiesPills}
            otherText={allergiesOther}
            onChange={setAllergiesPills}
            onOtherChange={setAllergiesOther}
          />

          {/* Alimentos evitados — multi-selección */}
          <label style={{ fontSize: 13, display: "block", marginBottom: 4 }}>Alimentos evitados</label>
          <PillSelect
            options={FOODS_AVOIDED_OPTIONS}
            selected={foodsAvoidedPills}
            otherText={foodsAvoidedOther}
            onChange={setFoodsAvoidedPills}
            onOtherChange={setFoodsAvoidedOther}
          />

          {/* Historial médico */}
          <label style={{ fontSize: 13 }}>Historial médico</label>
          <textarea
            name="medical_history"
            rows={2}
            defaultValue={profile?.medical_history ?? ""}
            style={{ ...inputStyle, minHeight: 48 }}
          />

          {/* Estilo dietario — multi-selección */}
          <label style={{ fontSize: 13, display: "block", marginBottom: 4 }}>Estilo dietario</label>
          <PillSelect
            options={DIETARY_STYLE_OPTIONS}
            selected={dietaryPills}
            otherText={dietaryOther}
            onChange={setDietaryPills}
            onOtherChange={setDietaryOther}
          />

          {/* Preferencias alimentarias */}
          <label style={{ fontSize: 13 }}>Preferencias alimentarias</label>
          <textarea
            name="food_preferences"
            rows={2}
            defaultValue={profile?.food_preferences ?? ""}
            style={{ ...inputStyle, minHeight: 48 }}
          />

          {/* Alimentos no deseados */}
          <label style={{ fontSize: 13 }}>Alimentos no deseados</label>
          <textarea
            name="disliked_foods"
            rows={2}
            defaultValue={profile?.disliked_foods ?? ""}
            style={{ ...inputStyle, minHeight: 48 }}
          />

          {/* Agua */}
          <label style={{ fontSize: 13 }}>Consumo de agua (L/día)</label>
          <input
            name="water_intake_liters"
            type="number"
            step="0.1"
            min="0"
            max="10"
            defaultValue={profile?.water_intake_liters ?? ""}
            style={inputStyle}
          />

          {/* Nivel de actividad */}
          <label style={{ fontSize: 13 }}>Nivel de actividad</label>
          <select name="activity_level" defaultValue={profile?.activity_level ?? ""} style={selectStyle}>
            <option value="">— Seleccionar —</option>
            <option value="Sedentario">Sedentario — sin ejercicio</option>
            <option value="Ligero">Ligero — 1-2 días/semana</option>
            <option value="Moderado">Moderado — 3-4 días/semana</option>
            <option value="Alto">Alto — 5-6 días/semana</option>
            <option value="Muy alto">Muy alto — atleta / entrenamiento diario</option>
          </select>

          {/* Estrés */}
          <label style={{ fontSize: 13 }}>Nivel de estrés</label>
          <select name="stress_level" defaultValue={profile?.stress_level ?? ""} style={selectStyle}>
            <option value="">— Seleccionar —</option>
            <option value="1">1 — Muy bajo</option>
            <option value="2">2 — Bajo</option>
            <option value="3">3 — Moderado</option>
            <option value="4">4 — Alto</option>
            <option value="5">5 — Muy alto</option>
          </select>

          {/* Calidad del sueño */}
          <label style={{ fontSize: 13 }}>Calidad del sueño</label>
          <select name="sleep_quality" defaultValue={profile?.sleep_quality ?? ""} style={selectStyle}>
            <option value="">— Seleccionar —</option>
            <option value="1">1 — Muy mala</option>
            <option value="2">2 — Mala</option>
            <option value="3">3 — Regular</option>
            <option value="4">4 — Buena</option>
            <option value="5">5 — Excelente</option>
          </select>

          {/* Horas de sueño */}
          <label style={{ fontSize: 13 }}>Horas de sueño por noche</label>
          <input
            name="sleep_hours"
            type="number"
            step="0.5"
            min="3"
            max="12"
            defaultValue={profile?.sleep_hours ?? ""}
            style={inputStyle}
          />

          {/* Presupuesto */}
          <label style={{ fontSize: 13 }}>Presupuesto para alimentación</label>
          <select name="budget_level" defaultValue={profile?.budget_level ?? ""} style={selectStyle}>
            <option value="">— Seleccionar —</option>
            <option value="Bajo">Bajo</option>
            <option value="Medio">Medio</option>
            <option value="Medio-alto">Medio-alto</option>
            <option value="Alto">Alto</option>
          </select>

          {/* Adherencia */}
          <label style={{ fontSize: 13 }}>Nivel de adherencia esperado</label>
          <select name="adherence_level" defaultValue={profile?.adherence_level ?? ""} style={selectStyle}>
            <option value="">— Seleccionar —</option>
            <option value="1">1 — Muy baja</option>
            <option value="2">2 — Baja</option>
            <option value="3">3 — Moderada</option>
            <option value="4">4 — Alta</option>
            <option value="5">5 — Muy alta</option>
          </select>

          {/* Días de ejercicio */}
          <label style={{ fontSize: 13 }}>Días de ejercicio por semana</label>
          <select
            name="exercise_frequency_per_week"
            defaultValue={profile?.exercise_frequency_per_week ?? ""}
            style={selectStyle}
          >
            <option value="">— Seleccionar —</option>
            {[0, 1, 2, 3, 4, 5, 6, 7].map((n) => (
              <option key={n} value={n}>
                {n} {n === 1 ? "día" : "días"}
              </option>
            ))}
          </select>

          {/* Tipo de ejercicio — multi-selección */}
          <label style={{ fontSize: 13, display: "block", marginBottom: 4 }}>Tipo de ejercicio</label>
          <PillSelect
            options={EXERCISE_TYPE_OPTIONS}
            selected={exerciseTypePills}
            otherText={exerciseTypeOther}
            onChange={setExerciseTypePills}
            onOtherChange={setExerciseTypeOther}
          />

          {/* Notas adicionales */}
          <label style={{ fontSize: 13 }}>Notas adicionales</label>
          <textarea
            name="extra_notes"
            rows={2}
            defaultValue={profile?.extra_notes ?? ""}
            style={{ ...inputStyle, minHeight: 48 }}
          />

          <button type="submit" style={{ marginTop: 8 }}>Guardar perfil</button>
        </form>
      )}

      {/* ── Métricas ─────────────────────────────────────────────────────── */}
      {tab === "metrics" && (
        <div>
          <form onSubmit={onAddMetric} style={{ maxWidth: 400, marginBottom: 24 }}>
            <h2 style={{ fontSize: 16 }}>Agregar medición</h2>
            <label style={{ fontSize: 13 }}>Peso (kg)</label>
            <input value={mWeight} onChange={(e) => setMWeight(e.target.value)} style={inputStyle} />
            <label style={{ fontSize: 13 }}>Talla (cm)</label>
            <input value={mHeight} onChange={(e) => setMHeight(e.target.value)} style={inputStyle} />
            <label style={{ fontSize: 13 }}>Notas</label>
            <input value={mNotes} onChange={(e) => setMNotes(e.target.value)} style={inputStyle} />
            <button type="submit">Agregar</button>
          </form>
          <table style={{ borderCollapse: "collapse", width: "100%", maxWidth: 800 }}>
            <thead>
              <tr style={{ textAlign: "left", borderBottom: "1px solid #ccc" }}>
                <th style={{ padding: 8 }}>Fecha</th>
                <th style={{ padding: 8 }}>Peso</th>
                <th style={{ padding: 8 }}>Talla</th>
                <th style={{ padding: 8 }}>Fuente</th>
              </tr>
            </thead>
            <tbody>
              {metrics.map((m) => (
                <tr key={m.id} style={{ borderBottom: "1px solid #eee" }}>
                  <td style={{ padding: 8 }}>{m.recorded_at}</td>
                  <td style={{ padding: 8 }}>{m.weight_kg ?? "—"}</td>
                  <td style={{ padding: 8 }}>{m.height_cm ?? "—"}</td>
                  <td style={{ padding: 8 }}>{m.source}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
