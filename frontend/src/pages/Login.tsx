import { useState, type FormEvent } from "react"
import { useNavigate, useLocation } from "react-router-dom"
import { useAuth } from "../context/AuthContext"
import Button from "../components/ui/Button"

export default function Login() {
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [error, setError] = useState("")
  const [loading, setLoading] = useState(false)
  const { login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  const from = (location.state as { from?: string })?.from || "/dashboard"

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError("")
    setLoading(true)
    try {
      await login(email, password)
      navigate(from, { replace: true })
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al iniciar sesión")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 px-4">
      <div className="w-full max-w-sm">
        {/* Logo + name */}
        <div className="mb-8 text-center">
          <img
            src="/logo-login.webp"
            alt="Dra. Acosta Nutribot"
            className="mx-auto mb-4 rounded-2xl shadow-md"
            width={180}
            height={174}
          />
          <h1 className="text-xl font-bold text-gray-800">Dra. Acosta</h1>
          <p className="text-sm text-gray-500">Nutribot — Gestión Nutricional</p>
        </div>

        {/* Login form */}
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
            placeholder="doctora@ejemplo.com"
            className="mb-4 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm
              focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
          />

          <label className="mb-1 block text-sm font-medium text-gray-700">
            Contraseña
          </label>
          <input
            type="password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="mb-6 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm
              focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
          />

          <Button type="submit" disabled={loading} className="w-full">
            {loading ? "Iniciando sesión..." : "Iniciar sesión"}
          </Button>
        </form>
      </div>
    </div>
  )
}
