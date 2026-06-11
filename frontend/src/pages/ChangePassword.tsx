import { type FormEvent, useState } from "react"
import { Navigate, useNavigate } from "react-router-dom"
import { Eye, EyeSlash } from "@phosphor-icons/react"
import { useAuth } from "../context/AuthContext"

export default function ChangePassword() {
  const { token, session, changePassword, logout } = useAuth()
  const navigate = useNavigate()
  const [currentPassword, setCurrentPassword] = useState("")
  const [newPassword, setNewPassword] = useState("")
  const [confirmPassword, setConfirmPassword] = useState("")
  const [showCurrent, setShowCurrent] = useState(false)
  const [showNew, setShowNew] = useState(false)
  const [showConfirm, setShowConfirm] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  if (!token) return <Navigate to="/login" replace />
  if (session && !session.mustChangePassword) {
    return <Navigate to="/dashboard" replace />
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    setError(null)
    if (newPassword !== confirmPassword) {
      setError("Las contraseñas nuevas no coinciden.")
      return
    }
    setLoading(true)
    try {
      await changePassword(currentPassword, newPassword)
      navigate("/dashboard", { replace: true })
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo cambiar la contraseña.")
    } finally {
      setLoading(false)
    }
  }

  const inputClass =
    "w-full rounded-lg border border-gray-300 px-3 py-2 pr-10 text-sm focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 px-4">
      <div className="w-full max-w-md rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
        <h1 className="text-xl font-bold text-gray-800">Crear nueva contraseña</h1>
        <p className="mt-2 text-sm text-gray-500 leading-relaxed">
          Por seguridad, antes de acceder al sistema debes reemplazar la contraseña
          temporal por una contraseña privada.
        </p>

        <form onSubmit={onSubmit} className="mt-6 space-y-4">
          {/* Current password */}
          <div>
            <label className="mb-1 block text-sm font-medium text-gray-700">
              Contraseña temporal o actual
            </label>
            <div className="relative">
              <input
                className={inputClass}
                type={showCurrent ? "text" : "password"}
                autoComplete="current-password"
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                required
              />
              <button
                type="button"
                onClick={() => setShowCurrent(!showCurrent)}
                className="absolute right-2.5 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 transition-colors"
                aria-label={showCurrent ? "Ocultar contraseña" : "Mostrar contraseña"}
                tabIndex={-1}
              >
                {showCurrent ? <EyeSlash size={18} /> : <Eye size={18} />}
              </button>
            </div>
          </div>

          {/* New password */}
          <div>
            <label className="mb-1 block text-sm font-medium text-gray-700">
              Nueva contraseña
            </label>
            <div className="relative">
              <input
                className={inputClass}
                type={showNew ? "text" : "password"}
                autoComplete="new-password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                minLength={8}
                required
              />
              <button
                type="button"
                onClick={() => setShowNew(!showNew)}
                className="absolute right-2.5 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 transition-colors"
                aria-label={showNew ? "Ocultar contraseña" : "Mostrar contraseña"}
                tabIndex={-1}
              >
                {showNew ? <EyeSlash size={18} /> : <Eye size={18} />}
              </button>
            </div>
          </div>

          {/* Confirm password */}
          <div>
            <label className="mb-1 block text-sm font-medium text-gray-700">
              Confirmar nueva contraseña
            </label>
            <div className="relative">
              <input
                className={inputClass}
                type={showConfirm ? "text" : "password"}
                autoComplete="new-password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                minLength={8}
                required
              />
              <button
                type="button"
                onClick={() => setShowConfirm(!showConfirm)}
                className="absolute right-2.5 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 transition-colors"
                aria-label={showConfirm ? "Ocultar contraseña" : "Mostrar contraseña"}
                tabIndex={-1}
              >
                {showConfirm ? <EyeSlash size={18} /> : <Eye size={18} />}
              </button>
            </div>
          </div>

          {error && <p className="text-sm text-red-600">{error}</p>}

          <div className="flex gap-3">
            <button
              type="submit"
              disabled={loading}
              className="rounded-full bg-emerald-600 px-6 py-2.5 text-sm font-semibold text-white hover:bg-emerald-700 active:scale-[0.98] disabled:opacity-50 transition-all"
            >
              {loading ? "Guardando..." : "Guardar contraseña"}
            </button>
            <button
              type="button"
              onClick={logout}
              className="rounded-full border border-gray-300 px-6 py-2.5 text-sm font-medium text-gray-600 hover:bg-gray-50 active:scale-[0.98] transition-all"
            >
              Salir
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
