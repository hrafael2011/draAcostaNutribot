import {
  type CSSProperties,
  type FormEvent,
  useEffect,
  useState,
} from "react"
import { Navigate, useLocation } from "react-router-dom"
import { useAuth } from "../context/AuthContext"
import { fetchRegistrationOpen, registerDoctor } from "../services/api"

export default function Login() {
  const { token, login } = useAuth()
  const location = useLocation()
  const from = (location.state as { from?: { pathname: string } })?.from
    ?.pathname

  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const [showRegister, setShowRegister] = useState(false)
  const [regName, setRegName] = useState("")
  const [regEmail, setRegEmail] = useState("")
  const [regPassword, setRegPassword] = useState("")
  const [regPhone, setRegPhone] = useState("")
  const [registrationOpen, setRegistrationOpen] = useState<boolean | null>(
    null,
  )

  useEffect(() => {
    let cancelled = false
    fetchRegistrationOpen()
      .then((r) => {
        if (!cancelled) setRegistrationOpen(r.open)
      })
      .catch(() => {
        if (!cancelled) setRegistrationOpen(false)
      })
    return () => {
      cancelled = true
    }
  }, [])

  if (token) {
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

  async function onRegister(e: FormEvent) {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      await registerDoctor({
        full_name: regName,
        email: regEmail,
        password: regPassword,
        phone: regPhone || undefined,
      })
      await login(regEmail, regPassword)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Registration error")
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
      {!showRegister ? (
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
          {registrationOpen === true && (
            <p style={{ marginTop: 16, fontSize: 14 }}>
              <button
                type="button"
                style={{
                  background: "none",
                  border: "none",
                  color: "#06c",
                  cursor: "pointer",
                  padding: 0,
                }}
                onClick={() => {
                  setShowRegister(true)
                  setError(null)
                }}
              >
                Create doctor account
              </button>
            </p>
          )}
        </form>
      ) : (
        <form onSubmit={onRegister}>
          <h2 style={{ fontSize: 18 }}>New account</h2>
          <label style={label}>Full name</label>
          <input
            style={input}
            value={regName}
            onChange={(e) => setRegName(e.target.value)}
            required
          />
          <label style={label}>Email</label>
          <input
            style={input}
            type="email"
            value={regEmail}
            onChange={(e) => setRegEmail(e.target.value)}
            required
          />
          <label style={label}>Password</label>
          <input
            style={input}
            type="password"
            value={regPassword}
            onChange={(e) => setRegPassword(e.target.value)}
            required
          />
          <label style={label}>Phone (optional)</label>
          <input
            style={input}
            value={regPhone}
            onChange={(e) => setRegPhone(e.target.value)}
          />
          {error && (
            <p style={{ color: "#b00020", fontSize: 14 }}>{error}</p>
          )}
          <button type="submit" disabled={loading} style={{ padding: "10px 16px" }}>
            {loading ? "Creating…" : "Register and sign in"}
          </button>
          <p style={{ marginTop: 16 }}>
            <button
              type="button"
              style={{ background: "none", border: "none", color: "#06c", cursor: "pointer" }}
              onClick={() => {
                setShowRegister(false)
                setError(null)
              }}
            >
              Back to login
            </button>
          </p>
        </form>
      )}
    </div>
  )
}
