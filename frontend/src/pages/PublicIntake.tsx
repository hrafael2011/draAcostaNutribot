import { type CSSProperties, FormEvent, useEffect, useMemo, useState } from "react"
import { useParams } from "react-router-dom"
import { submitIntakeForm, updateIntakeForm, validateIntakeToken } from "../services/api"
import type { IntakePublicMeta } from "../types"
import DatePicker from "../components/ui/DatePicker"
import NoAplicaField from "../components/ui/NoAplicaField"
import WeightInput from "../components/ui/WeightInput"
import HeightInput from "../components/ui/HeightInput"
import { OBJECTIVE_OPTIONS } from "../constants/objectives"

const COUNTRY_CITIES: Record<string, string[]> = {
  "República Dominicana": ["Santo Domingo", "Santiago", "La Romana", "San Pedro de Macorís", "Punta Cana"],
  Mexico: ["Ciudad de México", "Guadalajara", "Monterrey", "Puebla", "Mérida"],
  Colombia: ["Bogotá", "Medellín", "Cali", "Barranquilla", "Cartagena"],
  "Costa Rica": ["San José", "Alajuela", "Heredia", "Cartago", "Liberia"],
  USA: ["Miami", "New York", "Los Angeles", "Houston", "Orlando"],
}

export default function PublicIntake() {
  const { token } = useParams()
  const [meta, setMeta] = useState<IntakePublicMeta | null>(null)
  const [linkType, setLinkType] = useState<"register" | "update">("register")
  const [error, setError] = useState<string | null>(null)
  const [done, setDone] = useState(false)
  const [country, setCountry] = useState("")
  const [city, setCity] = useState("")
  const [birthDate, setBirthDate] = useState("")
  const [diseases, setDiseases] = useState("")
  const [medications, setMedications] = useState("")
  const [foodAllergies, setFoodAllergies] = useState("")
  const [foodsAvoided, setFoodsAvoided] = useState("")
  const [medicalHistory, setMedicalHistory] = useState("")
  const [weightKg, setWeightKg] = useState("")
  const [heightCm, setHeightCm] = useState("")
  const [objective, setObjective] = useState("")

  const cityOptions = useMemo(() => COUNTRY_CITIES[country] || [], [country])

  useEffect(() => {
    if (!token) return
    let cancelled = false
    validateIntakeToken(token)
      .then((m) => {
        if (!cancelled) {
          setMeta(m)
          if (m.link_type) setLinkType(m.link_type as "register" | "update")
        }
      })
      .catch((e) => {
        if (!cancelled) setError(e instanceof Error ? e.message : "Error")
      })
    return () => {
      cancelled = true
    }
  }, [token])

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    if (!token) return
    const form = e.target as HTMLFormElement
    const fd = new FormData(form)
    const str = (k: string) => (fd.get(k) as string)?.trim() || ""
    const optStr = (k: string) => {
      const v = str(k)
      return v === "" ? null : v
    }
    const weightKgNum = parseFloat(weightKg);
    const heightCmNum = parseFloat(heightCm);

    const weight_kg = !isNaN(weightKgNum) && weightKgNum > 0 ? weightKgNum : NaN;
    const height_cm = !isNaN(heightCmNum) && heightCmNum > 0 ? heightCmNum : NaN;

    setError(null)

    if (linkType === "update") {
      const updateBody: Record<string, unknown> = {}
      const firstName = str("first_name")
      const lastName = str("last_name")
      if (firstName) updateBody.first_name = firstName
      if (lastName) updateBody.last_name = lastName
      if (str("whatsapp")) updateBody.whatsapp = optStr("whatsapp")
      if (str("email")) updateBody.email = optStr("email")
      if (country) updateBody.country = country
      if (city) updateBody.city = city
      if (Number.isFinite(weight_kg)) updateBody.weight_kg = weight_kg
      if (Number.isFinite(height_cm)) updateBody.height_cm = height_cm
      try {
        await updateIntakeForm(token, updateBody)
        setDone(true)
      } catch (err) {
        setError(err instanceof Error ? err.message : "Update failed")
      }
      return
    }

    // Register flow — full submission
    const num = (k: string) => {
      const v = str(k)
      if (!v) return null
      const n = Number(v)
      return Number.isFinite(n) ? n : null
    }
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
      whatsapp: optStr("whatsapp"),
      email: optStr("email") || null,
      diseases: diseases === "No aplica" ? "No aplica" : diseases,
      medications: medications === "No aplica" ? "No aplica" : medications,
      medical_history: medicalHistory === "No aplica" ? "No aplica" : medicalHistory,
      dietary_style: optStr("dietary_style"),
      food_preferences: optStr("food_preferences"),
      disliked_foods: optStr("disliked_foods"),
      water_intake_liters: num("water_intake_liters"),
      stress_level: num("stress_level"),
      sleep_quality: num("sleep_quality"),
      sleep_hours: num("sleep_hours"),
      budget_level: optStr("budget_level"),
      activity_level: optStr("activity_level"),
      adherence_level: num("adherence_level"),
      exercise_frequency_per_week: num("exercise_frequency_per_week"),
      exercise_type: optStr("exercise_type"),
      extra_notes: optStr("extra_notes"),
    }
    if (!country || !(city || str("city_other"))) {
      setError("Country and city are required")
      return
    }
    if (!Number.isFinite(body.weight_kg as number) || !Number.isFinite(body.height_cm as number)) {
      setError("Weight and height are required in valid units")
      return
    }
    try {
      await submitIntakeForm(token, body)
      setDone(true)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Submit failed")
    }
  }

  const wrap: CSSProperties = {
    maxWidth: 720,
    margin: "24px auto",
    fontFamily: "system-ui, sans-serif",
    padding: 16,
  }
  const input: CSSProperties = {
    width: "100%",
    padding: 8,
    marginBottom: 10,
    boxSizing: "border-box",
  }

  if (!token) {
    return <p style={wrap}>Invalid link.</p>
  }
  if (error && !meta) {
    return (
      <div style={wrap}>
        <p style={{ color: "#b00020" }}>{error}</p>
      </div>
    )
  }
  if (!meta) {
    return <p style={wrap}>Checking link…</p>
  }
  if (!meta.valid) {
    return (
      <div style={wrap}>
        <h1>Link not available</h1>
        <p>{meta.message || "This intake link cannot be used."}</p>
      </div>
    )
  }
  if (done) {
    return (
      <div style={wrap}>
        <h1 style={{ marginTop: 0 }}>{linkType === "register" ? "¡Registro completado!" : "¡Datos actualizados!"}</h1>
        <p style={{ color: "#555" }}>
          {linkType === "register"
            ? "Tu información ha sido enviada correctamente. El equipo de la Dra. Acosta se pondrá en contacto contigo."
            : "Tus datos han sido actualizados correctamente."}
        </p>
      </div>
    )
  }

  return (
    <div style={wrap}>
      <h1 style={{ marginTop: 0 }}>Patient intake</h1>
      <p style={{ color: "#555" }}>
        {meta.patient_first_name || meta.patient_last_name
          ? `Hello ${meta.patient_first_name || ""} ${meta.patient_last_name || ""}`.trim()
          : "Please complete your information."}
      </p>
      {error && <p style={{ color: "#b00020" }}>{error}</p>}
      <form onSubmit={onSubmit}>
        <h2 style={{ fontSize: 16 }}>Personal</h2>
        <label style={{ fontSize: 13 }}>First name *</label>
        <input name="first_name" required style={input} />
        <label style={{ fontSize: 13 }}>Last name *</label>
        <input name="last_name" required style={input} />
        <label style={{ fontSize: 13 }}>Birth date *</label>
        <DatePicker
          value={birthDate}
          onChange={setBirthDate}
          name="birth_date"
          placeholder="DD/MM/AAAA"
          required
        />
        <label style={{ fontSize: 13 }}>Sex *</label>
        <input name="sex" required placeholder="e.g. female / male" style={input} />
        <label style={{ fontSize: 13 }}>Email</label>
        <input name="email" type="email" style={input} />
        <label style={{ fontSize: 13 }}>WhatsApp</label>
        <input name="whatsapp" style={input} />
        <label style={{ fontSize: 13 }}>Country *</label>
        <select value={country} onChange={(e) => { setCountry(e.target.value); setCity("") }} required style={input}>
          <option value="">Select country</option>
          {Object.keys(COUNTRY_CITIES).map((c) => (
            <option key={c} value={c}>
              {c}
            </option>
          ))}
        </select>
        <label style={{ fontSize: 13 }}>City *</label>
        {cityOptions.length > 0 ? (
          <select value={city} onChange={(e) => setCity(e.target.value)} required style={input}>
            <option value="">Select city</option>
            {cityOptions.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
            <option value="__other">Other city</option>
          </select>
        ) : (
          <input name="city_other" required style={input} placeholder="Type city" />
        )}
        {city === "__other" && (
          <input name="city_other" required style={input} placeholder="Type city" />
        )}

        <h2 style={{ fontSize: 16 }}>{linkType === "update" ? "Actualizar medidas" : "Measurements *"}</h2>
        <label style={{ fontSize: 13 }}>Peso{linkType === "register" ? " *" : ""}</label>
        <WeightInput valueKg={weightKg} onChangeKg={setWeightKg} name="weight_kg" required={linkType === "register"} />
        <label style={{ fontSize: 13, marginTop: 10 }}>Estatura{linkType === "register" ? " *" : ""}</label>
        <HeightInput valueCm={heightCm} onChangeCm={setHeightCm} name="height_cm" required={linkType === "register"} />
        {linkType === "register" && (
          <>
            <label style={{ fontSize: 13 }}>Neck (cm)</label>
            <input name="neck_cm" type="number" step="0.1" style={input} />
            <label style={{ fontSize: 13 }}>Chest (cm)</label>
            <input name="chest_cm" type="number" step="0.1" style={input} />
            <label style={{ fontSize: 13 }}>Waist (cm)</label>
            <input name="waist_cm" type="number" step="0.1" style={input} />
            <label style={{ fontSize: 13 }}>Hip (cm)</label>
            <input name="hip_cm" type="number" step="0.1" style={input} />
            <label style={{ fontSize: 13 }}>Leg (cm)</label>
            <input name="leg_cm" type="number" step="0.1" style={input} />
            <label style={{ fontSize: 13 }}>Calf (cm)</label>
            <input name="calf_cm" type="number" step="0.1" style={input} />
          </>
        )}

        {linkType === "register" && (
          <>
            <h2 style={{ fontSize: 16 }}>Goals & health</h2>
            <label style={{ fontSize: 13 }}>Main objective *</label>
            <select name="objective" value={objective} onChange={(e) => setObjective(e.target.value)} required style={input}>
              {OBJECTIVE_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>{o.label}</option>
              ))}
            </select>
            <NoAplicaField label="Diseases / diagnoses" value={diseases} onChange={setDiseases} name="diseases" placeholder="Ej. Diabetes tipo 2, Hipertensión" />
            <NoAplicaField label="Medications" value={medications} onChange={setMedications} name="medications" placeholder="Ej. Metformina 500mg, Losartán 50mg" />
            <NoAplicaField label="Food allergies" value={foodAllergies} onChange={setFoodAllergies} name="food_allergies" type="input" placeholder="Ej. Gluten, lactosa" />
            <NoAplicaField label="Foods avoided" value={foodsAvoided} onChange={setFoodsAvoided} name="foods_avoided" type="input" placeholder="Ej. Lácteos, gluten" />
            <NoAplicaField label="Medical history" value={medicalHistory} onChange={setMedicalHistory} name="medical_history" placeholder="Include diagnoses, surgeries, relevant events and current follow-up." />
            <label style={{ fontSize: 13 }}>Dietary style</label>
            <input name="dietary_style" style={input} />
            <label style={{ fontSize: 13 }}>Foods you like</label>
            <p style={{ fontSize: 12, color: "#666", marginTop: -6 }}>Be specific: preferred proteins, carbs, vegetables, fruits and usual preparations.</p>
            <textarea name="food_preferences" rows={2} style={{ ...input, minHeight: 48 }} />
            <label style={{ fontSize: 13 }}>Foods you dislike</label>
            <textarea name="disliked_foods" rows={2} style={{ ...input, minHeight: 48 }} />

            <h2 style={{ fontSize: 16 }}>Habits</h2>
            <label style={{ fontSize: 13 }}>Water (liters / day)</label>
            <input name="water_intake_liters" type="number" step="0.1" style={input} />
            <label style={{ fontSize: 13 }}>Activity level</label>
            <input name="activity_level" placeholder="e.g. low / moderate" style={input} />
            <label style={{ fontSize: 13 }}>Stress (1–5)</label>
            <input name="stress_level" type="number" style={input} />
            <label style={{ fontSize: 13 }}>Sleep quality (1–5)</label>
            <input name="sleep_quality" type="number" style={input} />
            <label style={{ fontSize: 13 }}>Sleep hours</label>
            <input name="sleep_hours" type="number" step="0.1" style={input} />
            <label style={{ fontSize: 13 }}>Budget level</label>
            <input name="budget_level" placeholder="e.g. medium" style={input} />
            <label style={{ fontSize: 13 }}>Expected adherence (1–5)</label>
            <p style={{ fontSize: 12, color: "#666", marginTop: -6 }}>1 = very hard to follow, 5 = very likely to follow consistently.</p>
            <input name="adherence_level" type="number" style={input} />
            <label style={{ fontSize: 13 }}>Exercise days / week</label>
            <input name="exercise_frequency_per_week" type="number" style={input} />
            <label style={{ fontSize: 13 }}>Exercise type</label>
            <input name="exercise_type" style={input} />
            <label style={{ fontSize: 13 }}>Anything else we should know</label>
            <textarea name="extra_notes" rows={2} style={{ ...input, minHeight: 48 }} />
          </>
        )}

        <button type="submit" style={{ padding: "12px 20px", marginTop: 8 }}>
          {linkType === "update" ? "Actualizar datos" : "Submit"}
        </button>
      </form>
    </div>
  )
}
