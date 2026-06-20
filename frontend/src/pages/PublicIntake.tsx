import { FormEvent, useEffect, useState } from "react"
import { useParams } from "react-router-dom"
import { submitIntakeForm, updateIntakeForm, validateIntakeToken } from "../services/api"
import type { IntakePublicMeta } from "../types"
import DatePicker from "../components/ui/DatePicker"
import LocationSelector from "../components/LocationSelector"
import ConfirmModal from "../components/ui/ConfirmModal"
import type { ChangeItem } from "../components/ui/ConfirmModal"

export default function PublicIntake() {
  const { token } = useParams()
  const [meta, setMeta] = useState<IntakePublicMeta | null>(null)
  const [linkType, setLinkType] = useState<"register" | "update">("register")
  const [error, setError] = useState<string | null>(null)
  const [done, setDone] = useState(false)
  const [country, setCountry] = useState("")
  const [city, setCity] = useState("")
  const [birthDate, setBirthDate] = useState("")
  const [weightKg, setWeightKg] = useState("")
  const [confirmOpen, setConfirmOpen] = useState(false)
  const [confirmChanges, setConfirmChanges] = useState<ChangeItem[]>([])
  const [confirmLoading, setConfirmLoading] = useState(false)
  const [pendingBody, setPendingBody] = useState<Record<string, unknown> | null>(null)

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

    setError(null)

    if (linkType === "update") {
      const weightKgNum = parseFloat(weightKg);
      const weight_kg = !isNaN(weightKgNum) && weightKgNum > 0 ? weightKgNum : NaN;
      const updateBody: Record<string, unknown> = {}
      const firstName = str("first_name")
      const lastName = str("last_name")
      if (firstName) updateBody.first_name = firstName
      if (lastName) updateBody.last_name = lastName
      if (str("whatsapp")) updateBody.whatsapp = optStr("whatsapp")
      if (country) updateBody.country = country
      if (city) updateBody.city = city
      if (Number.isFinite(weight_kg)) updateBody.weight_kg = weight_kg

      // Check if there are actual changes
      if (Object.keys(updateBody).length === 0) {
        setError("No hay cambios para guardar")
        return
      }

      // Show modal instead of direct submit
      const changes: ChangeItem[] = []
      if (firstName) changes.push({ label: "Nombre", newValue: firstName, isNew: true })
      if (lastName) changes.push({ label: "Apellido", newValue: lastName, isNew: true })
      if (updateBody.whatsapp) changes.push({ label: "WhatsApp", newValue: String(updateBody.whatsapp), isNew: true })
      if (updateBody.country) changes.push({ label: "País", newValue: String(updateBody.country), isNew: true })
      if (updateBody.city) changes.push({ label: "Ciudad", newValue: String(updateBody.city), isNew: true })
      if (updateBody.weight_kg) changes.push({ label: "Peso", newValue: String(updateBody.weight_kg), isNew: true })

      setPendingBody(updateBody)
      setConfirmChanges(changes)
      setConfirmOpen(true)
      return
    }

    // Register flow — show confirmation first
    const body: Record<string, unknown> = {
      first_name: str("first_name"),
      last_name: str("last_name"),
      birth_date: birthDate,
      sex: str("sex"),
      country,
      city,
      whatsapp: optStr("whatsapp"),
      email: optStr("email") || null,
    }
    if (!country || !city) {
      setError("País y ciudad son obligatorios")
      return
    }

    // Build changes for the modal
    const changes: ChangeItem[] = [
      { label: "Nombre", newValue: `${str("first_name")} ${str("last_name")}`, isNew: true },
      { label: "Fecha de nacimiento", newValue: birthDate, isNew: true },
      { label: "Sexo", newValue: str("sex"), isNew: true },
      { label: "País", newValue: country, isNew: true },
      { label: "Ciudad", newValue: city, isNew: true },
    ]
    if (str("whatsapp")) changes.push({ label: "WhatsApp", newValue: str("whatsapp"), isNew: true })
    if (str("email")) changes.push({ label: "Email", newValue: str("email"), isNew: true })

    setPendingBody(body)
    setConfirmChanges(changes)
    setConfirmOpen(true)
    return
  }

  async function handleRegisterConfirm() {
    if (!pendingBody || !token) return
    setConfirmLoading(true)
    try {
      await submitIntakeForm(token, pendingBody)
      setDone(true)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Submit failed")
    } finally {
      setConfirmLoading(false)
      setConfirmOpen(false)
      setPendingBody(null)
    }
  }

  async function handleUpdateConfirm() {
    if (!pendingBody || !token) return
    setConfirmLoading(true)
    try {
      await updateIntakeForm(token, pendingBody)
      setDone(true)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Update failed")
    } finally {
      setConfirmLoading(false)
      setConfirmOpen(false)
      setPendingBody(null)
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
                    : "Actualiza tu información personal y peso."}
                </p>
              </div>

              {/* Datos personales */}
              <section>
                <h2 className="text-xs font-semibold text-emerald-600 uppercase tracking-wider mb-4">Datos personales</h2>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {linkType !== "update" && (
                    <>
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
                    </>
                  )}
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
                    <select name="sex" required
                      className="w-full px-3.5 py-2.5 text-sm border border-slate-200 rounded-xl bg-white text-slate-800 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-colors">
                      <option value="">Seleccionar...</option>
                      <option value="Femenino">Femenino</option>
                      <option value="Masculino">Masculino</option>
                    </select>
                  </div>
                  {linkType === "register" && (
                    <div>
                      <label className="block text-sm font-medium text-slate-700 mb-1.5">Email</label>
                      <input name="email" type="email" placeholder="ejemplo@correo.com"
                        className="w-full px-3.5 py-2.5 text-sm border border-slate-200 rounded-xl bg-white text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-colors" />
                    </div>
                  )}
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1.5">WhatsApp</label>
                    <input name="whatsapp" placeholder="+54 11 1234 5678"
                      className="w-full px-3.5 py-2.5 text-sm border border-slate-200 rounded-xl bg-white text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-colors" />
                  </div>
                  <div className="sm:col-span-2">
                    <p className="text-xs text-slate-500 bg-slate-50 rounded-lg px-3 py-2">
                      El correo y WhatsApp nos ayudan a mantenerte al día con recordatorios y actualizaciones de tu plan.
                    </p>
                  </div>
                  <div className="sm:col-span-2">
                    <LocationSelector
                      country={country}
                      city={city}
                      onCountryChange={(c) => { setCountry(c); setCity("") }}
                      onCityChange={setCity}
                    />
                  </div>
                </div>
              </section>

              {/* Actualizar peso */}
              {linkType === "update" && (
                <section>
                  <h2 className="text-xs font-semibold text-emerald-600 uppercase tracking-wider mb-4">Actualizar peso</h2>
                  <div className="max-w-xs">
                    <label className="block text-sm font-medium text-slate-700 mb-1.5">Peso (kg)</label>
                    <input name="weight_kg" type="number" step="0.1" value={weightKg} onChange={(e) => setWeightKg(e.target.value)}
                      className="w-full px-3.5 py-2.5 text-sm border border-slate-200 rounded-xl bg-white text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-colors" />
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
      <ConfirmModal
        open={confirmOpen}
        title="Revisa tus datos"
        description="Confirmá que toda tu información sea correcta antes de enviarla."
        changes={confirmChanges}
        onConfirm={linkType === "register" ? handleRegisterConfirm : handleUpdateConfirm}
        onEdit={() => { setConfirmOpen(false); setPendingBody(null) }}
        confirmLabel="Confirmar y enviar"
        editLabel="Corregir"
        loading={confirmLoading}
      />
    </div>
  )
}
