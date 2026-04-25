import { type CSSProperties, type FormEvent, useState } from "react"
import { Navigate, useNavigate } from "react-router-dom"
import { useAuth } from "../context/AuthContext"

export default function ChangePassword() {
  const { token, session, changePassword, logout } = useAuth()
  const navigate = useNavigate()
  const [currentPassword, setCurrentPassword] = useState("")
  const [newPassword, setNewPassword] = useState("")
  const [confirmPassword, setConfirmPassword] = useState("")
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

  const box: CSSProperties = {
    maxWidth: 460,
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
      <h1 style={{ marginTop: 0 }}>Crear nueva contraseña</h1>
      <p style={{ color: "#555", fontSize: 14, lineHeight: 1.5 }}>
        Por seguridad, antes de acceder al sistema debes reemplazar la contraseña
        temporal por una contraseña privada.
      </p>
      <form onSubmit={onSubmit}>
        <label style={label}>Contraseña temporal o actual</label>
        <input
          style={input}
          type="password"
          autoComplete="current-password"
          value={currentPassword}
          onChange={(e) => setCurrentPassword(e.target.value)}
          required
        />
        <label style={label}>Nueva contraseña</label>
        <input
          style={input}
          type="password"
          autoComplete="new-password"
          value={newPassword}
          onChange={(e) => setNewPassword(e.target.value)}
          minLength={8}
          required
        />
        <label style={label}>Confirmar nueva contraseña</label>
        <input
          style={input}
          type="password"
          autoComplete="new-password"
          value={confirmPassword}
          onChange={(e) => setConfirmPassword(e.target.value)}
          minLength={8}
          required
        />
        {error && <p style={{ color: "#b00020", fontSize: 14 }}>{error}</p>}
        <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
          <button type="submit" disabled={loading} style={{ padding: "10px 16px" }}>
            {loading ? "Guardando..." : "Guardar contraseña"}
          </button>
          <button type="button" onClick={logout} style={{ padding: "10px 16px" }}>
            Salir
          </button>
        </div>
      </form>
    </div>
  )
}
