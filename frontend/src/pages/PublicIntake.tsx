import { FormEvent, useEffect, useMemo, useState } from "react"
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
      setError("País y ciudad son obligatorios")
      return
    }
    if (!Number.isFinite(body.weight_kg as number) || !Number.isFinite(body.height_cm as number)) {
      setError("Peso y altura son obligatorios en unidades válidas")
      return
    }
    try {
      await submitIntakeForm(token, body)
      setDone(true)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Submit failed")
    }
  }

  if (!token) {
    return (
      <div className="min-h-screen bg-slate-50">
        <div className="max-w-2xl mx-auto px-4 py-8">
          <div className="bg-white rounded-2xl shadow-sm border border-slate-100 p-8 text-center">
            <h1 className="text-xl font-bold text-slate-800 mb-2">Enlace no disponible</h1>
            <p className="text-sm text-slate-500">Enlace inválido.</p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <div className="max-w-2xl mx-auto px-4 py-8">
        {/* Error banner before meta loads */}
        {error && !meta && (
          <div className="mb-6 rounded-2xl bg-red-50 border border-red-200 px-5 py-4 flex items-center justify-between">
            <p className="text-sm text-red-700">{error}</p>
          </div>
        )}

        {/* Loading */}
        {!meta && !error && (
          <div className="text-center py-12 text-sm text-slate-400">Verificando enlace...</div>
        )}

        {/* Invalid link */}
        {meta && !meta.valid && (
          <div className="bg-white rounded-2xl shadow-sm border border-slate-100 p-8 text-center">
            <h1 className="text-xl font-bold text-slate-800 mb-2">Enlace no disponible</h1>
            <p className="text-sm text-slate-500">{meta.message || "Este enlace no se puede utilizar."}</p>
          </div>
        )}

        {/* Success */}
        {meta && meta.valid && done && (
          <div className="bg-white rounded-2xl shadow-sm border border-emerald-100 p-8 text-center">
            <img
              src="/logo-doctora.jpeg"
              alt="Dra. Acosta"
              className="h-24 w-auto mx-auto mb-4 object-contain"
            />
            <h1 className="text-xl font-bold text-emerald-800 mb-2">
              {linkType === "register" ? "¡Registro completado!" : "¡Datos actualizados!"}
            </h1>
            <p className="text-sm text-slate-600">
              {linkType === "register"
                ? "Tu información ha sido enviada correctamente. El equipo de la Dra. Acosta se pondrá en contacto contigo."
                : "Tus datos han sido actualizados correctamente."}
            </p>
          </div>
        )}

        {/* Form */}
        {meta && meta.valid && !done && (
          <form onSubmit={onSubmit}>
            <div className="bg-white rounded-2xl shadow-sm border border-slate-100 p-6 md:p-8 space-y-8">
              {/* Error banner inside form */}
              {error && (
                <div className="rounded-2xl bg-red-50 border border-red-200 px-5 py-4">
                  <p className="text-sm text-red-700">{error}</p>
                </div>
              )}

              {/* Header */}
              <div className="text-center">
                <img
                  src="/logo-doctora.jpeg"
                  alt="Dra. Acosta"
                  className="h-28 w-auto mx-auto mb-4 object-contain"
                />
                <h1 className="text-2xl font-bold text-slate-900">
                  {linkType === "register" ? "Registro de Paciente" : "Actualizar Datos"}
                </h1>
                <p className="text-sm text-slate-500 mt-1">
                  {linkType === "register"
                    ? "Completa tus datos para tu plan personalizado con la Dra. Acosta."
                    : "Actualiza tu información personal y medidas corporales."}
                </p>
              </div>

              {/* Datos personales */}
              <section>
                <h2 className="text-xs font-semibold text-emerald-600 uppercase tracking-wider mb-4">Datos personales</h2>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1.5">
                      Nombre <span className="text-red-500">*</span>
                    </label>
                    <input name="first_name" required
                      className="w-full px-3.5 py-2.5 text-sm border border-slate-200 rounded-xl bg-white text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-colors" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1.5">
                      Apellido <span className="text-red-500">*</span>
                    </label>
                    <input name="last_name" required
                      className="w-full px-3.5 py-2.5 text-sm border border-slate-200 rounded-xl bg-white text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-colors" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1.5">
                      Fecha de nacimiento <span className="text-red-500">*</span>
                    </label>
                    <DatePicker value={birthDate} onChange={setBirthDate} name="birth_date" required />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1.5">
                      Sexo <span className="text-red-500">*</span>
                    </label>
                    <input name="sex" required placeholder="Ej. Femenino / Masculino"
                      className="w-full px-3.5 py-2.5 text-sm border border-slate-200 rounded-xl bg-white text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-colors" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1.5">Email</label>
                    <input name="email" type="email" placeholder="ejemplo@correo.com"
                      className="w-full px-3.5 py-2.5 text-sm border border-slate-200 rounded-xl bg-white text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-colors" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1.5">WhatsApp</label>
                    <input name="whatsapp" placeholder="+54 11 1234 5678"
                      className="w-full px-3.5 py-2.5 text-sm border border-slate-200 rounded-xl bg-white text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-colors" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1.5">
                      País <span className="text-red-500">*</span>
                    </label>
                    <select value={country} onChange={(e) => { setCountry(e.target.value); setCity("") }} required
                      className="w-full px-3.5 py-2.5 text-sm border border-slate-200 rounded-xl bg-white text-slate-800 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-colors">
                      <option value="">Seleccionar país</option>
                      {Object.keys(COUNTRY_CITIES).map((c) => <option key={c} value={c}>{c}</option>)}
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1.5">
                      Ciudad <span className="text-red-500">*</span>
                    </label>
                    {cityOptions.length > 0 ? (
                      <select value={city} onChange={(e) => setCity(e.target.value)} required
                        className="w-full px-3.5 py-2.5 text-sm border border-slate-200 rounded-xl bg-white text-slate-800 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-colors">
                        <option value="">Seleccionar ciudad</option>
                        {cityOptions.map((c) => <option key={c} value={c}>{c}</option>)}
                        <option value="__other">Otra ciudad</option>
                      </select>
                    ) : (
                      <input name="city_other" required placeholder="Escribe tu ciudad"
                        className="w-full px-3.5 py-2.5 text-sm border border-slate-200 rounded-xl bg-white text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-colors" />
                    )}
                    {city === "__other" && (
                      <input name="city_other" required placeholder="Escribe tu ciudad"
                        className="w-full px-3.5 py-2.5 text-sm border border-slate-200 rounded-xl bg-white text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-colors mt-2" />
                    )}
                  </div>
                </div>
              </section>

              {/* Medidas corporales */}
              <section>
                <h2 className="text-xs font-semibold text-emerald-600 uppercase tracking-wider mb-4">
                  {linkType === "update" ? "Actualizar medidas" : "Medidas corporales"}
                </h2>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1.5">
                      Peso {linkType === "register" && <span className="text-red-500">*</span>}
                    </label>
                    <WeightInput valueKg={weightKg} onChangeKg={setWeightKg} name="weight_kg" required={linkType === "register"} />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1.5">
                      Altura {linkType === "register" && <span className="text-red-500">*</span>}
                    </label>
                    <HeightInput valueCm={heightCm} onChangeCm={setHeightCm} name="height_cm" required={linkType === "register"} />
                  </div>
                </div>
                {/* Only show extra body measurements for register */}
                {linkType === "register" && (
                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 mt-4">
                    {["neck_cm", "chest_cm", "waist_cm", "hip_cm", "leg_cm", "calf_cm"].map((field) => (
                      <div key={field}>
                        <label className="block text-sm font-medium text-slate-700 mb-1.5">
                          {field === "neck_cm" ? "Cuello" : field === "chest_cm" ? "Pecho" : field === "waist_cm" ? "Cintura" : field === "hip_cm" ? "Cadera" : field === "leg_cm" ? "Pierna" : "Pantorrilla"} (cm)
                        </label>
                        <input name={field} type="number" step="0.1"
                          className="w-full px-3.5 py-2.5 text-sm border border-slate-200 rounded-xl bg-white text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-colors" />
                      </div>
                    ))}
                  </div>
                )}
              </section>

              {/* Salud y objetivo — only for register */}
              {linkType === "register" && (
                <section>
                  <h2 className="text-xs font-semibold text-emerald-600 uppercase tracking-wider mb-4">Salud y objetivo</h2>
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-slate-700 mb-1.5">
                        Objetivo principal <span className="text-red-500">*</span>
                      </label>
                      <select name="objective" value={objective} onChange={(e) => setObjective(e.target.value)} required
                        className="w-full px-3.5 py-2.5 text-sm border border-slate-200 rounded-xl bg-white text-slate-800 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-colors">
                        {OBJECTIVE_OPTIONS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
                      </select>
                    </div>
                    <NoAplicaField label="Enfermedades / diagnósticos" value={diseases} onChange={setDiseases} name="diseases" placeholder="Ej. Diabetes tipo 2, Hipertensión" />
                    <NoAplicaField label="Medicamentos" value={medications} onChange={setMedications} name="medications" placeholder="Ej. Metformina 500mg" />
                    <NoAplicaField label="Alergias alimentarias" value={foodAllergies} onChange={setFoodAllergies} name="food_allergies" type="input" placeholder="Ej. Gluten, lactosa" required />
                    <NoAplicaField label="Alimentos a evitar" value={foodsAvoided} onChange={setFoodsAvoided} name="foods_avoided" type="input" placeholder="Ej. Lácteos, gluten" required />
                    <NoAplicaField label="Historial médico" value={medicalHistory} onChange={setMedicalHistory} name="medical_history" placeholder="Cirugías, diagnósticos, eventos relevantes..." />
                    <div>
                      <label className="block text-sm font-medium text-slate-700 mb-1.5">Estilo de alimentación</label>
                      <input name="dietary_style" placeholder="Ej. Omnívoro, Vegetariano, Keto..."
                        className="w-full px-3.5 py-2.5 text-sm border border-slate-200 rounded-xl bg-white text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-colors" />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-slate-700 mb-1.5">Alimentos que te gustan</label>
                      <p className="text-xs text-slate-500 mb-2">Proteínas, carbohidratos, verduras, frutas y preparaciones habituales.</p>
                      <textarea name="food_preferences" rows={2}
                        className="w-full px-3.5 py-2.5 text-sm border border-slate-200 rounded-xl bg-white text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-colors resize-none" />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-slate-700 mb-1.5">Alimentos que NO te gustan</label>
                      <textarea name="disliked_foods" rows={2}
                        className="w-full px-3.5 py-2.5 text-sm border border-slate-200 rounded-xl bg-white text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-colors resize-none" />
                    </div>
                  </div>
                </section>
              )}

              {/* Hábitos — only for register */}
              {linkType === "register" && (
                <section>
                  <h2 className="text-xs font-semibold text-emerald-600 uppercase tracking-wider mb-4">Hábitos</h2>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-slate-700 mb-1.5">Agua (litros / día)</label>
                      <input name="water_intake_liters" type="number" step="0.1" placeholder="Ej. 2"
                        className="w-full px-3.5 py-2.5 text-sm border border-slate-200 rounded-xl bg-white text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-colors" />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-slate-700 mb-1.5">Nivel de actividad</label>
                      <input name="activity_level" placeholder="Ej. Bajo / Moderado / Alto"
                        className="w-full px-3.5 py-2.5 text-sm border border-slate-200 rounded-xl bg-white text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-colors" />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-slate-700 mb-1.5">Estrés (1-5)</label>
                      <input name="stress_level" type="number" min="1" max="5" placeholder="1-5"
                        className="w-full px-3.5 py-2.5 text-sm border border-slate-200 rounded-xl bg-white text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-colors" />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-slate-700 mb-1.5">Calidad del sueño (1-5)</label>
                      <input name="sleep_quality" type="number" min="1" max="5" placeholder="1-5"
                        className="w-full px-3.5 py-2.5 text-sm border border-slate-200 rounded-xl bg-white text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-colors" />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-slate-700 mb-1.5">Horas de sueño</label>
                      <input name="sleep_hours" type="number" step="0.5" placeholder="Ej. 7"
                        className="w-full px-3.5 py-2.5 text-sm border border-slate-200 rounded-xl bg-white text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-colors" />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-slate-700 mb-1.5">Presupuesto</label>
                      <input name="budget_level" placeholder="Ej. Bajo / Medio / Alto"
                        className="w-full px-3.5 py-2.5 text-sm border border-slate-200 rounded-xl bg-white text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-colors" />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-slate-700 mb-1.5">Adherencia esperada (1-5)</label>
                      <p className="text-xs text-slate-500 mb-1">1 = muy difícil, 5 = muy probable de seguir</p>
                      <input name="adherence_level" type="number" min="1" max="5" placeholder="1-5"
                        className="w-full px-3.5 py-2.5 text-sm border border-slate-200 rounded-xl bg-white text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-colors" />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-slate-700 mb-1.5">Ejercicio (días / semana)</label>
                      <input name="exercise_frequency_per_week" type="number" min="0" max="7" placeholder="0-7"
                        className="w-full px-3.5 py-2.5 text-sm border border-slate-200 rounded-xl bg-white text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-colors" />
                    </div>
                    <div className="sm:col-span-2">
                      <label className="block text-sm font-medium text-slate-700 mb-1.5">Tipo de ejercicio</label>
                      <input name="exercise_type" placeholder="Ej. Fuerza, Cardio, Yoga, Caminata..."
                        className="w-full px-3.5 py-2.5 text-sm border border-slate-200 rounded-xl bg-white text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-colors" />
                    </div>
                    <div className="sm:col-span-2">
                      <label className="block text-sm font-medium text-slate-700 mb-1.5">Algo más que debamos saber</label>
                      <textarea name="extra_notes" rows={2}
                        className="w-full px-3.5 py-2.5 text-sm border border-slate-200 rounded-xl bg-white text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-colors resize-none" />
                    </div>
                  </div>
                </section>
              )}

              {/* Submit */}
              <div className="pt-4">
                <button type="submit"
                  className="w-full rounded-full bg-emerald-600 px-6 py-3 text-sm font-semibold text-white hover:bg-emerald-700 active:scale-[0.98] transition-all shadow-sm">
                  {linkType === "update" ? "Actualizar datos" : "Enviar registro"}
                </button>
                <p className="text-xs text-slate-400 text-center mt-4">
                  🔒 Tus datos están protegidos y solo serán usados para tu plan nutricional personalizado.
                </p>
              </div>
            </div>
          </form>
        )}
      </div>
    </div>
  )
}
