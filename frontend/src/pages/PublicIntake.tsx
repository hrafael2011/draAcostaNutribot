import { type CSSProperties, FormEvent, useEffect, useState } from "react"
import { useParams } from "react-router-dom"
import { submitIntakeForm, validateIntakeToken } from "../services/api"
import type { IntakePublicMeta } from "../types"

export default function PublicIntake() {
  const { token } = useParams()
  const [meta, setMeta] = useState<IntakePublicMeta | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [done, setDone] = useState(false)

  useEffect(() => {
    if (!token) return
    let cancelled = false
    validateIntakeToken(token)
      .then((m) => {
        if (!cancelled) setMeta(m)
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
    const num = (k: string, required: boolean) => {
      const v = str(k)
      if (!v) return required ? NaN : null
      const n = Number(v)
      return Number.isFinite(n) ? n : null
    }
    const body: Record<string, unknown> = {
      first_name: str("first_name"),
      last_name: str("last_name"),
      birth_date: str("birth_date"),
      sex: str("sex"),
      country: str("country"),
      city: str("city"),
      objective: str("objective"),
      food_allergies: str("food_allergies"),
      foods_avoided: str("foods_avoided"),
      weight_kg: num("weight_kg", true),
      height_cm: num("height_cm", true),
      whatsapp: optStr("whatsapp"),
      email: optStr("email") || null,
      diseases: optStr("diseases"),
      medications: optStr("medications"),
      medical_history: optStr("medical_history"),
      dietary_style: optStr("dietary_style"),
      food_preferences: optStr("food_preferences"),
      disliked_foods: optStr("disliked_foods"),
      water_intake_liters: num("water_intake_liters", false),
      stress_level: num("stress_level", false),
      sleep_quality: num("sleep_quality", false),
      sleep_hours: num("sleep_hours", false),
      budget_level: optStr("budget_level"),
      activity_level: optStr("activity_level"),
      adherence_level: num("adherence_level", false),
      exercise_frequency_per_week: num("exercise_frequency_per_week", false),
      exercise_type: optStr("exercise_type"),
      extra_notes: optStr("extra_notes"),
      neck_cm: num("neck_cm", false),
      chest_cm: num("chest_cm", false),
      waist_cm: num("waist_cm", false),
      hip_cm: num("hip_cm", false),
      leg_cm: num("leg_cm", false),
      calf_cm: num("calf_cm", false),
    }
    if (!Number.isFinite(body.weight_kg as number) || !Number.isFinite(body.height_cm as number)) {
      setError("Weight and height are required")
      return
    }
    setError(null)
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
        <h1>Thank you</h1>
        <p>Your information was submitted successfully.</p>
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
        <input name="birth_date" type="date" required style={input} />
        <label style={{ fontSize: 13 }}>Sex *</label>
        <input name="sex" required placeholder="e.g. female / male" style={input} />
        <label style={{ fontSize: 13 }}>Email</label>
        <input name="email" type="email" style={input} />
        <label style={{ fontSize: 13 }}>WhatsApp</label>
        <input name="whatsapp" style={input} />
        <label style={{ fontSize: 13 }}>Country *</label>
        <input name="country" required style={input} />
        <label style={{ fontSize: 13 }}>City *</label>
        <input name="city" required style={input} />

        <h2 style={{ fontSize: 16 }}>Measurements *</h2>
        <label style={{ fontSize: 13 }}>Weight (kg) *</label>
        <input name="weight_kg" type="number" step="0.1" required style={input} />
        <label style={{ fontSize: 13 }}>Height (cm) *</label>
        <input name="height_cm" type="number" step="0.1" required style={input} />
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

        <h2 style={{ fontSize: 16 }}>Goals & health</h2>
        <label style={{ fontSize: 13 }}>Main objective *</label>
        <input name="objective" required placeholder="e.g. lose_weight" style={input} />
        <label style={{ fontSize: 13 }}>Diseases / diagnoses</label>
        <textarea name="diseases" rows={2} style={{ ...input, minHeight: 48 }} />
        <label style={{ fontSize: 13 }}>Medications</label>
        <textarea name="medications" rows={2} style={{ ...input, minHeight: 48 }} />
        <label style={{ fontSize: 13 }}>Food allergies * (or &quot;none&quot;)</label>
        <input name="food_allergies" required style={input} />
        <label style={{ fontSize: 13 }}>Foods avoided * (or &quot;none&quot;)</label>
        <input name="foods_avoided" required style={input} />
        <label style={{ fontSize: 13 }}>Medical history</label>
        <textarea name="medical_history" rows={2} style={{ ...input, minHeight: 48 }} />
        <label style={{ fontSize: 13 }}>Dietary style</label>
        <input name="dietary_style" style={input} />
        <label style={{ fontSize: 13 }}>Foods you like</label>
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
        <label style={{ fontSize: 13 }}>Adherence (1–5)</label>
        <input name="adherence_level" type="number" style={input} />
        <label style={{ fontSize: 13 }}>Exercise days / week</label>
        <input name="exercise_frequency_per_week" type="number" style={input} />
        <label style={{ fontSize: 13 }}>Exercise type</label>
        <input name="exercise_type" style={input} />
        <label style={{ fontSize: 13 }}>Anything else we should know</label>
        <textarea name="extra_notes" rows={2} style={{ ...input, minHeight: 48 }} />

        <button type="submit" style={{ padding: "12px 20px", marginTop: 8 }}>
          Submit
        </button>
      </form>
    </div>
  )
}
