import {
  type CSSProperties,
  type FormEvent,
  useState,
} from "react"
import { Navigate, useLocation } from "react-router-dom"
import { useAuth } from "../context/AuthContext"

export default function Login() {
  const { token, session, login } = useAuth()
  const location = useLocation()
  const from = (location.state as { from?: { pathname: string } })?.from
    ?.pathname

  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  if (token) {
    if (session?.mustChangePassword) {
      return <Navigate to="/change-password" replace />
    }
    return <Navigate to={from || "/dashboard"} replace />
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      await login(email, password)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login error")
    } finally {
      setLoading(false)
    }
  }

  const box: CSSProperties = {
    maxWidth: 420,
    margin: "10vh auto",
    fontFamily: "system-ui, sans-serif",
    padding: 24,
    border: "1px solid #ddd",
    borderRadius: 8,
  }
  const label: CSSProperties = { display: "block", fontSize: 13, marginBottom: 4 }
  const input: CSSProperties = {
    width: "100%",
    padding: "8px 10px",
    marginBottom: 12,
    boxSizing: "border-box",
  }

  return (
    <div style={box}>
      <h1 style={{ marginTop: 0 }}>Diet Admin</h1>
      <form onSubmit={onSubmit}>
        <label style={label}>Email</label>
        <input
          style={input}
          type="email"
          autoComplete="username"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />
        <label style={label}>Password</label>
        <input
          style={input}
          type="password"
          autoComplete="current-password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />
        {error && (
          <p style={{ color: "#b00020", fontSize: 14 }}>{error}</p>
        )}
        <button type="submit" disabled={loading} style={{ padding: "10px 16px" }}>
          {loading ? "Signing in…" : "Sign in"}
        </button>
        <p style={{ color: "#666", fontSize: 13, lineHeight: 1.5 }}>
          Las cuentas son creadas por el administrador del sistema.
        </p>
      </form>
    </div>
  )
}
