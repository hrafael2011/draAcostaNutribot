import { useEffect, useState, type FormEvent } from "react"
import { useNavigate, useSearchParams } from "react-router-dom"
import Button from "../components/ui/Button"

type PageState = "verifying" | "invalid" | "form" | "success" | "error"

export default function ResetPassword() {
  const [searchParams] = useSearchParams()
  const token = searchParams.get("token") || ""
  const navigate = useNavigate()

  const [state, setState] = useState<PageState>("verifying")
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [confirm, setConfirm] = useState("")
  const [errorMsg, setErrorMsg] = useState("")

  const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8002/api"

  useEffect(() => {
    if (!token) {
      setState("invalid")
      return
    }
    fetch(`${API_BASE}/auth/verify-reset-token?token=${encodeURIComponent(token)}`)
      .then((r) => r.json())
      .then((data) => {
        if (data.valid) {
          setEmail(data.email || "")
          setState("form")
        } else {
          setState("invalid")
        }
      })
      .catch(() => setState("invalid"))
  }, [token, API_BASE])

  const isValid =
    password.length >= 8 &&
    /[A-Z]/.test(password) &&
    /[0-9]/.test(password) &&
    password === confirm

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    if (!isValid) return
    setErrorMsg("")
    try {
      const res = await fetch(`${API_BASE}/auth/reset-password`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token, new_password: password }),
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: "Error" }))
        throw new Error(err.detail || "Error al restablecer la contraseña")
      }
      setState("success")
      setTimeout(() => navigate("/login", { replace: true }), 3000)
    } catch (err) {
      setErrorMsg(err instanceof Error ? err.message : "Error al restablecer la contraseña")
      setState("error")
    }
  }

  if (state === "verifying") {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-50 px-4">
        <div className="text-center">
          <div className="mx-auto mb-4 h-8 w-8 animate-spin rounded-full border-4 border-emerald-500 border-t-transparent" />
          <p className="text-gray-500">Verificando enlace...</p>
        </div>
      </div>
    )
  }

  if (state === "invalid") {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-50 px-4">
        <div className="w-full max-w-sm text-center">
          <img src="/logo-login.png" alt="Dra. Acosta" className="mx-auto mb-6" width={120} height={116} />
          <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
            <h1 className="mb-2 text-lg font-bold text-gray-800">Enlace inválido</h1>
            <p className="mb-6 text-sm text-gray-500">
              Este enlace ha expirado o no es válido. Solicita uno nuevo desde la página de inicio de sesión.
            </p>
            <Button onClick={() => navigate("/login")} className="w-full">
              Ir a iniciar sesión
            </Button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 px-4">
      <div className="w-full max-w-sm">
        <div className="mb-8 text-center">
          <img src="/logo-login.png" alt="Dra. Acosta" className="mx-auto mb-4" width={180} height={174} />
          <h1 className="text-xl font-bold text-gray-800">Dra. Acosta</h1>
          <p className="text-sm text-gray-500">Nutrisoft — Gestión Nutricional</p>
        </div>

        {state === "success" ? (
          <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm text-center">
            <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-emerald-100">
              <span className="text-xl text-emerald-600">✓</span>
            </div>
            <h2 className="mb-2 text-lg font-bold text-gray-800">Contraseña cambiada</h2>
            <p className="text-sm text-gray-500">
              Redirigiendo al inicio de sesión...
            </p>
          </div>
        ) : (
          <form
            onSubmit={handleSubmit}
            className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm"
          >
            <h2 className="mb-1 text-lg font-bold text-gray-800">Restablecer contraseña</h2>
            <p className="mb-4 text-sm text-gray-500">
              {email ? `Para: ${email}` : "Ingresa tu nueva contraseña"}
            </p>

            {(state === "error" || errorMsg) && (
              <div className="mb-4 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">
                {errorMsg}
              </div>
            )}

            <label className="mb-1 block text-sm font-medium text-gray-700">
              Nueva contraseña
            </label>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Mínimo 8 caracteres"
              className="mb-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm
                focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
            />
            <div className="mb-4 text-xs text-gray-400">
              Mín. 8 caracteres, al menos 1 mayúscula y 1 número
            </div>

            <label className="mb-1 block text-sm font-medium text-gray-700">
              Confirmar nueva contraseña
            </label>
            <input
              type="password"
              required
              value={confirm}
              onChange={(e) => setConfirm(e.target.value)}
              placeholder="Repite la contraseña"
              className="mb-6 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm
                focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
            />

            <Button type="submit" disabled={!isValid} className="w-full">
              Cambiar Contraseña
            </Button>
          </form>
        )}
      </div>
    </div>
  )
}
