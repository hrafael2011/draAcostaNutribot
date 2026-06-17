import { FormEvent, useCallback, useEffect, useState } from "react"
import {
  createAdminDoctor,
  getAdminDoctors,
  resetAdminDoctorPassword,
  updateAdminDoctor,
} from "../services/api"
import type { DoctorOut } from "../types"
import Button from "../components/ui/Button"
import { Badge } from "../components/ui/Badge"
import { Users, Plus, X, Copy } from "@phosphor-icons/react"
import { useAuth } from "../context/AuthContext"

type Role = "admin" | "doctor"

export default function AdminUsers() {
  const [doctors, setDoctors] = useState<DoctorOut[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [message, setMessage] = useState<string | null>(null)
  const [lastGeneratedPassword, setLastGeneratedPassword] = useState<string | null>(null)

  // Create modal
  const [showCreate, setShowCreate] = useState(false)
  const [createName, setCreateName] = useState("")
  const [createEmail, setCreateEmail] = useState("")
  const [createRole, setCreateRole] = useState<Role>("doctor")
  const [creating, setCreating] = useState(false)

  // Reset modal
  const [resetDoctor, setResetDoctor] = useState<DoctorOut | null>(null)
  const [resetting, setResetting] = useState(false)
  const [filter, setFilter] = useState<"all" | "active" | "inactive">("all")
  const { session: currentSession } = useAuth()
  const isSuperAdmin = currentSession?.role === "super_admin"

  const load = useCallback(() => {
    setError(null)
    setLoading(true)
    getAdminDoctors()
      .then(setDoctors)
      .catch((err) =>
        setError(err instanceof Error ? err.message : "No se pudieron cargar usuarios."),
      )
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => { load() }, [load])

  async function onCreate(e: FormEvent) {
    e.preventDefault()
    setError(null)
    setCreating(true)
    try {
      const result = await createAdminDoctor({
        full_name: createName,
        email: createEmail,
        role: createRole,
      })
      setLastGeneratedPassword(result.generated_password)
      setMessage("Usuario creado exitosamente.")
      setShowCreate(false)
      setCreateName(""); setCreateEmail(""); setCreateRole("doctor")
      load()
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo crear el usuario.")
    } finally {
      setCreating(false)
    }
  }

  async function onResetPassword(e: FormEvent) {
    e.preventDefault()
    if (!resetDoctor) return
    setError(null)
    setResetting(true)
    try {
      const result = await resetAdminDoctorPassword(resetDoctor.id)
      setLastGeneratedPassword(result.generated_password)
      setMessage(`Contraseña reseteada para ${resetDoctor.full_name}.`)
      setResetDoctor(null)
      load()
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo resetear la contraseña.")
    } finally {
      setResetting(false)
    }
  }

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">Usuarios del Sistema</h1>
          <p className="mt-1 text-sm text-gray-500">
            Gestiona doctores y administradores
          </p>
        </div>
        <Button onClick={() => setShowCreate(true)}>
          <Plus size={18} className="mr-1" /> Nuevo Usuario
        </Button>
      </div>

      {message && (
        <div className="mb-4 rounded-lg bg-emerald-50 px-4 py-3 text-sm text-emerald-700 border border-emerald-200">
          {message}
          {lastGeneratedPassword && (
            <div className="mt-2 flex items-center gap-2">
              <code className="rounded bg-white px-2 py-1 font-mono font-bold text-gray-800 border text-xs">
                {lastGeneratedPassword}
              </code>
              <button
                type="button"
                onClick={() => navigator.clipboard?.writeText(lastGeneratedPassword || "")}
                className="text-emerald-600 hover:text-emerald-700"
                title="Copiar"
              >
                <Copy size={14} />
              </button>
            </div>
          )}
        </div>
      )}
      {error && (
        <div className="mb-4 rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700 border border-red-200">
          {error}
        </div>
      )}

      {loading ? (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-14 animate-pulse rounded-lg bg-gray-100" />
          ))}
        </div>
      ) : doctors.length === 0 ? (
        <div className="rounded-xl border border-dashed border-gray-300 p-12 text-center">
          <Users size={48} className="mx-auto mb-3 text-gray-300" />
          <p className="text-gray-500">No hay usuarios registrados</p>
          <Button className="mt-4" onClick={() => setShowCreate(true)}>
            Crear primer usuario
          </Button>
        </div>
      ) : (
        <>
        <div className="mb-3 flex gap-2">
          {(["all", "active", "inactive"] as const).map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`rounded-full px-3 py-1 text-xs font-medium transition-colors ${
                filter === f
                  ? "bg-emerald-600 text-white"
                  : "bg-gray-100 text-gray-600 hover:bg-gray-200"
              }`}
            >
              {f === "all" ? "Todos" : f === "active" ? "Activos" : "Inactivos"}
            </button>
          ))}
        </div>
        <div className="overflow-x-auto rounded-xl border border-gray-200">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200 bg-gray-50 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                <th className="px-4 py-3">Nombre</th>
                <th className="px-4 py-3">Email</th>
                <th className="px-4 py-3">Rol</th>
                <th className="px-4 py-3">Estado</th>
                <th className="px-4 py-3">Creado</th>
                <th className="px-4 py-3 text-right">Acciones</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {doctors
                .filter((d) => filter === "all" || (filter === "active" ? d.is_active : !d.is_active))
                .filter((d) => isSuperAdmin || d.role !== "admin")
                .map((doctor) => (
                <tr key={doctor.id} className="hover:bg-gray-50 transition-colors">
                  <td className="px-4 py-3 font-medium text-gray-800">{doctor.full_name}</td>
                  <td className="px-4 py-3 text-gray-500">{doctor.email}</td>
                  <td className="px-4 py-3">
                    <Badge variant={doctor.role === "admin" || doctor.role === "super_admin" ? "neutral" : "info"}>
                      {doctor.role === "super_admin" ? "Super Admin" : doctor.role === "admin" ? "Admin" : "Doctor"}
                    </Badge>
                  </td>
                  <td className="px-4 py-3">
                    <Badge variant={doctor.is_active ? "success" : "danger"}>
                      {doctor.is_active ? "Activo" : "Inactivo"}
                    </Badge>
                  </td>
                  <td className="px-4 py-3 text-xs text-gray-400">
                    {doctor.created_at
                      ? new Date(doctor.created_at).toLocaleDateString("es-ES")
                      : "—"}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <div className="flex items-center justify-end gap-2">
                      <Button variant="ghost" size="sm"
                        onClick={() => {
                          setDoctors((prev) =>
                            prev.map((d) =>
                              d.id === doctor.id ? { ...d, is_active: !d.is_active } : d,
                            ),
                          )
                          updateAdminDoctor(doctor.id, { is_active: !doctor.is_active })
                            .catch(() => { load(); setError("Error al cambiar estado") })
                        }}>
                        {doctor.is_active ? "Desactivar" : "Activar"}
                      </Button>
                      <Button variant="secondary" size="sm" onClick={() => {
                        setResetDoctor(doctor)
                      }}>
                        Reset pass
                      </Button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        </>
      )}

      {/* Create modal */}
      {showCreate && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4"
          onClick={() => setShowCreate(false)}>
          <div className="w-full max-w-md rounded-xl bg-white p-6 shadow-lg"
            onClick={(e) => e.stopPropagation()}>
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-lg font-bold text-gray-800">Crear Usuario</h2>
              <button onClick={() => setShowCreate(false)} className="text-gray-400 hover:text-gray-600">
                <X size={20} />
              </button>
            </div>
            <form onSubmit={onCreate}>
              <div className="mb-3">
                <label className="mb-1 block text-sm font-medium text-gray-700">Nombre completo</label>
                <input required value={createName} onChange={(e) => setCreateName(e.target.value)}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm
                    focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500" />
              </div>
              <div className="mb-3">
                <label className="mb-1 block text-sm font-medium text-gray-700">Correo electrónico</label>
                <input required type="email" value={createEmail} onChange={(e) => setCreateEmail(e.target.value)}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm
                    focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500" />
              </div>
              <div className="mb-3">
                <label className="mb-1 block text-sm font-medium text-gray-700">Rol</label>
                <select value={createRole} onChange={(e) => setCreateRole(e.target.value as Role)}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm
                    focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500">
                  <option value="doctor">Doctor</option>
                  {isSuperAdmin && <option value="admin">Admin</option>}
                </select>
              </div>
              <div className="mb-4 rounded-lg bg-amber-50 p-3 border border-amber-200">
                <div className="text-xs text-gray-500">
                  La contraseña se generará automáticamente y se mostrará al crear el usuario.
                </div>
              </div>
              <div className="flex justify-end gap-2">
                <Button variant="secondary" type="button" onClick={() => setShowCreate(false)}>
                  Cancelar
                </Button>
                <Button type="submit" disabled={creating}>
                  {creating ? "Creando..." : "Crear Usuario"}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Reset password modal */}
      {resetDoctor && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4"
          onClick={() => setResetDoctor(null)}>
          <div className="w-full max-w-md rounded-xl bg-white p-6 shadow-lg"
            onClick={(e) => e.stopPropagation()}>
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-lg font-bold text-gray-800">Resetear Contraseña</h2>
              <button onClick={() => setResetDoctor(null)} className="text-gray-400 hover:text-gray-600">
                <X size={20} />
              </button>
            </div>
            <p className="mb-4 text-sm text-gray-600">
              ¿Resetear contraseña de <strong>{resetDoctor.full_name}</strong>?
            </p>
            <div className="mb-4 rounded-lg bg-amber-50 p-3 border border-amber-200">
              <div className="text-xs text-gray-500">
                Se generará una nueva contraseña automáticamente y se mostrará al confirmar.
              </div>
            </div>
            <div className="mb-4 rounded-lg bg-red-50 p-3 text-xs text-red-700 border border-red-200">
              Al resetear, el usuario será forzado a cambiar su contraseña en el próximo inicio de sesión.
            </div>
            <form onSubmit={onResetPassword}>
              <div className="flex justify-end gap-2">
                <Button variant="secondary" type="button" onClick={() => setResetDoctor(null)}>
                  Cancelar
                </Button>
                <Button variant="danger" type="submit" disabled={resetting}>
                  {resetting ? "Reseteando..." : "Resetear Contraseña"}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
