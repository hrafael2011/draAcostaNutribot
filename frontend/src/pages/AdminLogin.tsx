import { useState, type FormEvent } from "react"
import { useNavigate } from "react-router-dom"
import { useAuth } from "../context/AuthContext"
import { Eye, EyeSlash } from "@phosphor-icons/react"
import Button from "../components/ui/Button"

export default function AdminLogin() {
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState("")
  const [loading, setLoading] = useState(false)
  const [forgotOpen, setForgotOpen] = useState(false)
  const [forgotEmail, setForgotEmail] = useState("")
  const [forgotMessage, setForgotMessage] = useState<string | null>(null)
  const [forgotLoading, setForgotLoading] = useState(false)
  const { login, forgotPassword } = useAuth()
  const navigate = useNavigate()

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError("")
    setLoading(true)
    try {
      await login(email, password, "admin")
      navigate("/admin/users", { replace: true })
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al iniciar sesión")
    } finally {
      setLoading(false)
    }
  }

  const handleForgotSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setForgotLoading(true)
    setForgotMessage(null)
    try {
      const result = await forgotPassword(forgotEmail)
      setForgotMessage(result.message)
    } catch {
      setForgotMessage("Si el correo existe, recibirás instrucciones")
    } finally {
      setForgotLoading(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 px-4">
      <div className="w-full max-w-sm">
        <div className="mb-8 text-center">
          <img
            src="/logo-login.png"
            alt="Dra. Acosta Nutrisoft"
            className="mx-auto mb-4"
            width={180}
            height={174}
          />
          <h1 className="text-xl font-bold text-gray-800">Admin • Dra. Acosta</h1>
          <p className="text-sm text-gray-500">Panel de administración</p>
        </div>

        <form
          onSubmit={handleSubmit}
          className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm"
        >
          {error && (
            <div className="mb-4 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">
              {error}
            </div>
          )}

          <label className="mb-1 block text-sm font-medium text-gray-700">
            Correo electrónico
          </label>
          <input
            type="email"
            required
            autoFocus
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="admin@clinica.com"
            className="mb-4 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm
              focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
          />

          <label className="mb-1 block text-sm font-medium text-gray-700">
            Contraseña
          </label>
          <div className="relative mb-4">
            <input
              type={showPassword ? "text" : "password"}
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 pr-10 text-sm
                focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute right-2.5 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 transition-colors"
              aria-label={showPassword ? "Ocultar contraseña" : "Mostrar contraseña"}
              tabIndex={-1}
            >
              {showPassword ? <EyeSlash size={18} /> : <Eye size={18} />}
            </button>
          </div>

          <Button type="submit" disabled={loading} className="w-full">
            {loading ? "Iniciando sesión..." : "Iniciar sesión"}
          </Button>

          <div className="mt-3 text-center">
            <button
              type="button"
              onClick={() => setForgotOpen(true)}
              className="text-sm text-emerald-600 hover:text-emerald-700 hover:underline"
            >
              ¿Olvidaste tu contraseña?
            </button>
          </div>
        </form>
      </div>

      {/* Forgot password modal */}
      {forgotOpen && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4"
          onClick={() => setForgotOpen(false)}
        >
          <div
            className="w-full max-w-sm rounded-xl bg-white p-6 shadow-lg"
            onClick={(e) => e.stopPropagation()}
          >
            <h2 className="mb-2 text-lg font-bold text-gray-800">
              Recuperar contraseña
            </h2>
            <p className="mb-4 text-sm text-gray-500">
              Ingresa tu correo y te enviaremos un enlace para restablecer tu contraseña.
            </p>
            {forgotMessage ? (
              <>
                <div className="mb-4 rounded-lg bg-emerald-50 px-3 py-2 text-sm text-emerald-700">
                  {forgotMessage}
                </div>
                <Button
                  variant="secondary"
                  onClick={() => { setForgotOpen(false); setForgotMessage(null); }}
                  className="w-full"
                >
                  Cerrar
                </Button>
              </>
            ) : (
              <form onSubmit={handleForgotSubmit}>
                <input
                  type="email"
                  required
                  value={forgotEmail}
                  onChange={(e) => setForgotEmail(e.target.value)}
                  placeholder="admin@clinica.com"
                  className="mb-4 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm
                    focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
                />
                <Button type="submit" disabled={forgotLoading} className="w-full">
                  {forgotLoading ? "Enviando..." : "Enviar enlace"}
                </Button>
              </form>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
