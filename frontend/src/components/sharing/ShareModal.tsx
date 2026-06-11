import { useState } from "react"
import { AnimatePresence, motion } from "framer-motion"
import { X, Spinner, Check, Copy, WhatsappLogo, Envelope } from "@phosphor-icons/react"
import { createIntakeLink } from "../../services/api"
import { useToast } from "../../context/ToastContext"
import type { IntakeLink } from "../../types"

type ShareModalProps = {
  open: boolean
  onClose: () => void
  patientId: number
  patientName: string
}

const MESSAGES = {
  wa: "Hola%2C%20la%20Dra.%20Acosta%20te%20invita%20a%20completar%20tu%20ficha%20nutricional%20para%20tu%20plan%20personalizado%3A",
  emailSubject: "Completa tu ficha nutricional - Dra. Acosta",
  emailBody:
    "Hola,%0D%0A%0D%0ALa Dra. Acosta te comparte este link para que completes tu información nutricional y así preparar tu plan personalizado:%0D%0A%0D%0A",
}

const EXPIRATION_OPTIONS = [
  { value: 1, label: "1 día" },
  { value: 3, label: "3 días" },
  { value: 7, label: "7 días" },
  { value: 14, label: "14 días" },
  { value: 30, label: "30 días" },
]

export default function ShareModal({ open, onClose, patientId, patientName }: ShareModalProps) {
  const [link, setLink] = useState<IntakeLink | null>(null)
  const [selectedDays, setSelectedDays] = useState(7)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)
  const { addToast } = useToast()

  const handleCreate = async () => {
    setLoading(true)
    setError(null)
    try {
      const result = await createIntakeLink({ patient_id: patientId, expires_in_days: selectedDays })
      setLink(result)
      addToast("Formulario creado exitosamente", "success")
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error al crear el formulario")
    } finally {
      setLoading(false)
    }
  }

  const handleCopy = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text)
    } catch {
      const input = document.createElement("input")
      input.value = text
      document.body.appendChild(input)
      input.select()
      document.execCommand("copy")
      document.body.removeChild(input)
    }
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const url = link ? `${window.location.origin}/intake/${link.token}` : ""
  const waLink = `https://wa.me/?text=${MESSAGES.wa}%0A%0A${encodeURIComponent(url)}`
  const emailLink = `mailto:?subject=${encodeURIComponent(MESSAGES.emailSubject)}&body=${MESSAGES.emailBody}${encodeURIComponent(url)}`

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/20 backdrop-blur-sm"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={onClose}
        >
          <motion.div
            className="w-full max-w-md mx-4 bg-white rounded-2xl shadow-xl"
            initial={{ opacity: 0, y: 16, scale: 0.96 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 16, scale: 0.96 }}
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header */}
            <div className="flex items-center justify-between px-6 pt-6 pb-4">
              <h2 className="text-lg font-semibold text-gray-900">
                Enviar Formulario a {patientName}
              </h2>
              <button
                type="button"
                onClick={onClose}
                className="rounded-full p-1.5 text-gray-400 hover:bg-gray-100 hover:text-gray-600 transition-colors"
              >
                <X size={20} weight="bold" />
              </button>
            </div>

            {!link ? (
              /* Step 1 — Create */
              <div className="px-6 pb-6 space-y-5">
                <p className="text-sm text-gray-600 leading-relaxed">
                  El paciente podrá llenar sus datos personales, historial médico, medidas corporales y preferencias alimentarias.
                </p>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1.5">
                    El enlace expirará en
                  </label>
                  <select
                    value={selectedDays}
                    onChange={(e) => setSelectedDays(Number(e.target.value))}
                    className="w-full rounded-xl border border-gray-300 px-3 py-2.5 text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                  >
                    {EXPIRATION_OPTIONS.map((opt) => (
                      <option key={opt.value} value={opt.value}>
                        {opt.label}
                      </option>
                    ))}
                  </select>
                </div>

                {error && (
                  <div className="rounded-xl bg-red-50 border border-red-200 px-4 py-3 flex items-center justify-between">
                    <p className="text-sm text-red-700">{error}</p>
                  </div>
                )}

                <button
                  type="button"
                  onClick={handleCreate}
                  disabled={loading}
                  className="w-full flex items-center justify-center gap-2 rounded-full bg-emerald-600 px-6 py-3 text-sm font-semibold text-white hover:bg-emerald-700 disabled:opacity-60 disabled:cursor-not-allowed transition-colors shadow-sm"
                >
                  {loading ? (
                    <>
                      <Spinner size={18} className="animate-spin" />
                      Creando...
                    </>
                  ) : (
                    "Crear formulario"
                  )}
                </button>

                {error && (
                  <div className="flex justify-center">
                    <button
                      type="button"
                      onClick={handleCreate}
                      className="text-sm font-medium text-red-600 hover:text-red-700 underline"
                    >
                      Reintentar
                    </button>
                  </div>
                )}
              </div>
            ) : (
              /* Step 2 — Share */
              <div className="px-6 pb-6 space-y-4">
                <div className="flex items-center gap-2 rounded-xl border border-gray-200 bg-gray-50 px-4 py-3">
                  <input
                    type="text"
                    readOnly
                    value={url}
                    className="flex-1 bg-transparent text-sm text-gray-600 truncate outline-none"
                  />
                  <button
                    type="button"
                    onClick={() => handleCopy(url)}
                    className="shrink-0 flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-medium text-gray-500 hover:bg-gray-200 transition-colors"
                  >
                    {copied ? (
                      <>
                        <Check size={14} weight="bold" className="text-emerald-600" />
                        <span className="text-emerald-600">¡Copiado!</span>
                      </>
                    ) : (
                      <>
                        <Copy size={14} />
                        Copiar
                      </>
                    )}
                  </button>
                </div>

                <div className="flex gap-3">
                  <a
                    href={waLink}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex flex-1 items-center justify-center gap-2 rounded-xl bg-green-500 px-4 py-3 text-sm font-semibold text-white hover:bg-green-600 transition-colors shadow-sm"
                  >
                    <WhatsappLogo size={18} weight="fill" />
                    WhatsApp
                  </a>
                  <a
                    href={emailLink}
                    className="flex flex-1 items-center justify-center gap-2 rounded-xl bg-gray-600 px-4 py-3 text-sm font-semibold text-white hover:bg-gray-700 transition-colors shadow-sm"
                  >
                    <Envelope size={18} />
                    Correo
                  </a>
                </div>
              </div>
            )}
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
