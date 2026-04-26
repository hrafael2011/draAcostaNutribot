import { FormEvent, useCallback, useEffect, useState } from "react"
import {
  createAdminDoctor,
  getAdminDoctors,
  resetAdminDoctorPassword,
  updateAdminDoctor,
} from "../services/api"
import type { DoctorOut } from "../types"

type Role = "admin" | "doctor"

export default function AdminUsers() {
  const [doctors, setDoctors] = useState<DoctorOut[]>([])
  const [error, setError] = useState<string | null>(null)
  const [message, setMessage] = useState<string | null>(null)
  const [creating, setCreating] = useState(false)
  const [savingId, setSavingId] = useState<number | null>(null)
  const [resetId, setResetId] = useState<number | null>(null)
  const [newDoctor, setNewDoctor] = useState({
    full_name: "",
    email: "",
    phone: "",
    role: "doctor" as Role,
    temporary_password: "",
  })
  const [resetPassword, setResetPassword] = useState("")

  const load = useCallback(() => {
    setError(null)
    getAdminDoctors()
      .then(setDoctors)
      .catch((err) =>
        setError(err instanceof Error ? err.message : "No se pudieron cargar usuarios."),
      )
  }, [])

  useEffect(() => {
    load()
  }, [load])

  async function onCreate(e: FormEvent) {
    e.preventDefault()
    setError(null)
    setMessage(null)
    try {
      await createAdminDoctor({
        ...newDoctor,
        phone: newDoctor.phone || null,
      })
      setNewDoctor({
        full_name: "",
        email: "",
        phone: "",
        role: "doctor",
        temporary_password: "",
      })
      setCreating(false)
      setMessage("Cuenta creada. Al iniciar sesion debera crear su contrasena privada.")
      load()
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo crear la cuenta.")
    }
  }

  async function saveDoctor(doctor: DoctorOut) {
    setSavingId(doctor.id)
    setError(null)
    setMessage(null)
    try {
      await updateAdminDoctor(doctor.id, {
        full_name: doctor.full_name,
        email: doctor.email,
        phone: doctor.phone || null,
        role: doctor.role as Role,
        is_active: doctor.is_active,
      })
      setMessage("Usuario actualizado.")
      load()
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo actualizar.")
    } finally {
      setSavingId(null)
    }
  }

  async function onResetPassword(e: FormEvent) {
    e.preventDefault()
    if (resetId == null) return
    setError(null)
    setMessage(null)
    try {
      await resetAdminDoctorPassword(resetId, resetPassword)
      setResetPassword("")
      setResetId(null)
      setMessage("Contrasena temporal asignada. El usuario debera cambiarla al entrar.")
      load()
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo resetear la contrasena.")
    }
  }

  function patchLocal(id: number, body: Partial<DoctorOut>) {
    setDoctors((items) =>
      items.map((doctor) =>
        doctor.id === id ? { ...doctor, ...body } : doctor,
      ),
    )
  }

  return (
    <div>
      <h1 style={{ marginTop: 0 }}>Usuarios del sistema</h1>
      <p style={{ color: "#555", maxWidth: 760, lineHeight: 1.5 }}>
        Crea y administra accesos internos. Las contrasenas asignadas aqui son
        temporales: cada usuario debe crear su propia contrasena privada al entrar.
      </p>

      <div style={{ margin: "20px 0" }}>
        <button type="button" onClick={() => setCreating((value) => !value)}>
          {creating ? "Cancelar" : "Crear usuario"}
        </button>
      </div>

      {creating && (
        <form
          onSubmit={onCreate}
          style={{
            border: "1px solid #ddd",
            borderRadius: 8,
            padding: 16,
            marginBottom: 24,
            maxWidth: 540,
          }}
        >
          <h2 style={{ fontSize: 18, marginTop: 0 }}>Nuevo usuario</h2>
          <Field label="Nombre completo">
            <input
              required
              value={newDoctor.full_name}
              onChange={(e) =>
                setNewDoctor({ ...newDoctor, full_name: e.target.value })
              }
              style={inputStyle}
            />
          </Field>
          <Field label="Email">
            <input
              required
              type="email"
              value={newDoctor.email}
              onChange={(e) =>
                setNewDoctor({ ...newDoctor, email: e.target.value })
              }
              style={inputStyle}
            />
          </Field>
          <Field label="Telefono">
            <input
              value={newDoctor.phone}
              onChange={(e) =>
                setNewDoctor({ ...newDoctor, phone: e.target.value })
              }
              style={inputStyle}
            />
          </Field>
          <Field label="Rol">
            <select
              value={newDoctor.role}
              onChange={(e) =>
                setNewDoctor({ ...newDoctor, role: e.target.value as Role })
              }
              style={inputStyle}
            >
              <option value="doctor">Doctor</option>
              <option value="admin">Admin</option>
            </select>
          </Field>
          <Field label="Contrasena temporal">
            <input
              required
              type="password"
              minLength={8}
              value={newDoctor.temporary_password}
              onChange={(e) =>
                setNewDoctor({
                  ...newDoctor,
                  temporary_password: e.target.value,
                })
              }
              style={inputStyle}
            />
          </Field>
          <button type="submit">Crear con contrasena temporal</button>
        </form>
      )}

      {message && <p style={{ color: "#256029" }}>{message}</p>}
      {error && <p style={{ color: "#b00020" }}>{error}</p>}

      <table style={{ borderCollapse: "collapse", width: "100%", maxWidth: 1100 }}>
        <thead>
          <tr style={{ textAlign: "left", borderBottom: "1px solid #ccc" }}>
            <th style={cellStyle}>Nombre</th>
            <th style={cellStyle}>Email</th>
            <th style={cellStyle}>Rol</th>
            <th style={cellStyle}>Estado</th>
            <th style={cellStyle}>Seguridad</th>
            <th style={cellStyle}>Telegram</th>
            <th style={cellStyle}>Acciones</th>
          </tr>
        </thead>
        <tbody>
          {doctors.map((doctor) => (
            <tr key={doctor.id} style={{ borderBottom: "1px solid #eee" }}>
              <td style={cellStyle}>
                <input
                  value={doctor.full_name}
                  onChange={(e) =>
                    patchLocal(doctor.id, { full_name: e.target.value })
                  }
                  style={inlineInputStyle}
                />
              </td>
              <td style={cellStyle}>
                <input
                  type="email"
                  value={doctor.email}
                  onChange={(e) => patchLocal(doctor.id, { email: e.target.value })}
                  style={inlineInputStyle}
                />
              </td>
              <td style={cellStyle}>
                <select
                  value={doctor.role}
                  onChange={(e) =>
                    patchLocal(doctor.id, { role: e.target.value })
                  }
                  style={inlineInputStyle}
                >
                  <option value="doctor">Doctor</option>
                  <option value="admin">Admin</option>
                </select>
              </td>
              <td style={cellStyle}>
                <label style={{ display: "flex", gap: 6, alignItems: "center" }}>
                  <input
                    type="checkbox"
                    checked={doctor.is_active}
                    onChange={(e) =>
                      patchLocal(doctor.id, { is_active: e.target.checked })
                    }
                  />
                  {doctor.is_active ? "Activo" : "Inactivo"}
                </label>
              </td>
              <td style={cellStyle}>
                {doctor.must_change_password ? "Cambio pendiente" : "OK"}
              </td>
              <td style={cellStyle}>
                {doctor.telegram_username ||
                  doctor.telegram_user_id ||
                  "Sin vincular"}
              </td>
              <td style={cellStyle}>
                <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                  <button
                    type="button"
                    disabled={savingId === doctor.id}
                    onClick={() => saveDoctor(doctor)}
                  >
                    {savingId === doctor.id ? "Guardando..." : "Guardar"}
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setResetId(doctor.id)
                      setResetPassword("")
                    }}
                  >
                    Reset pass
                  </button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {resetId != null && (
        <form
          onSubmit={onResetPassword}
          style={{
            border: "1px solid #ddd",
            borderRadius: 8,
            padding: 16,
            marginTop: 24,
            maxWidth: 460,
          }}
        >
          <h2 style={{ fontSize: 18, marginTop: 0 }}>Resetear contrasena</h2>
          <p style={{ color: "#555", fontSize: 14 }}>
            Esta sera temporal. El usuario debera cambiarla al iniciar sesion.
          </p>
          <Field label="Nueva contrasena temporal">
            <input
              required
              minLength={8}
              type="password"
              value={resetPassword}
              onChange={(e) => setResetPassword(e.target.value)}
              style={inputStyle}
            />
          </Field>
          <div style={{ display: "flex", gap: 8 }}>
            <button type="submit">Asignar temporal</button>
            <button type="button" onClick={() => setResetId(null)}>
              Cancelar
            </button>
          </div>
        </form>
      )}
    </div>
  )
}

function Field({
  label,
  children,
}: {
  label: string
  children: React.ReactNode
}) {
  return (
    <label style={{ display: "block", fontSize: 13, marginBottom: 10 }}>
      {label}
      {children}
    </label>
  )
}

const inputStyle = {
  width: "100%",
  padding: 8,
  marginTop: 4,
  boxSizing: "border-box" as const,
}

const inlineInputStyle = {
  padding: 6,
  minWidth: 130,
  maxWidth: 220,
  boxSizing: "border-box" as const,
}

const cellStyle = { padding: 8, verticalAlign: "top" as const }
