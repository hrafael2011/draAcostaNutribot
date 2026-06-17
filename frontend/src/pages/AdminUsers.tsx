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
import { Users, Plus, X, Copy, ArrowsClockwise } from "@phosphor-icons/react"

type Role = "admin" | "doctor"

function generatePassword(): string {
  const chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
  let result = ""
  for (let i = 0; i < 10; i++) {
    result += chars.charAt(Math.floor(Math.random() * chars.length))
  }
  if (!/[A-Z]/.test(result)) result = "A" + result.slice(1)
  if (!/[0-9]/.test(result)) result = "5" + result.slice(1)
  return result
}

export default function AdminUsers() {
  const [doctors, setDoctors] = useState<DoctorOut[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [message, setMessage] = useState<string | null>(null)

  // Create modal
  const [showCreate, setShowCreate] = useState(false)
  const [createName, setCreateName] = useState("")
  const [createEmail, setCreateEmail] = useState("")
  const [createRole, setCreateRole] = useState<Role>("doctor")
  const [generatedPassword, setGeneratedPassword] = useState(generatePassword())
  const [creating, setCreating] = useState(false)

  // Reset modal
  const [resetDoctor, setResetDoctor] = useState<DoctorOut | null>(null)
  const [resetGeneratedPass, setResetGeneratedPass] = useState(generatePassword())
  const [resetting, setResetting] = useState(false)

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
      setMessage(`Usuario creado. Contraseña: ${result.generated_password}`)
      setShowCreate(false)
      setCreateName(""); setCreateEmail(""); setCreateRole("doctor")
      setGeneratedPassword(generatePassword())
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
      setMessage(`Contraseña reseteada para ${resetDoctor.full_name}. Nueva: ${result.generated_password}`)
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
        <Button onClick={() => { setShowCreate(true); setGeneratedPassword(generatePassword()) }}>
          <Plus size={18} className="mr-1" /> Nuevo Usuario
        </Button>
      </div>

      {message && (
        <div className="mb-4 rounded-lg bg-emerald-50 px-4 py-3 text-sm text-emerald-700 border border-emerald-200">
          {message}
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
          <Button className="mt-4" onClick={() => { setShowCreate(true); setGeneratedPassword(generatePassword()) }}>
            Crear primer usuario
          </Button>
        </div>
      ) : (
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
              {doctors.map((doctor) => (
                <tr key={doctor.id} className="hover:bg-gray-50 transition-colors">
                  <td className="px-4 py-3 font-medium text-gray-800">{doctor.full_name}</td>
                  <td className="px-4 py-3 text-gray-500">{doctor.email}</td>
                  <td className="px-4 py-3">
                    <Badge variant={doctor.role === "admin" ? "neutral" : "info"}>
                      {doctor.role === "admin" ? "Admin" : "Doctor"}
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
                        setResetGeneratedPass(generatePassword())
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
                  <option value="admin">Admin</option>
                </select>
              </div>
              <div className="mb-4 rounded-lg bg-amber-50 p-3 border border-amber-200">
                <div className="mb-1 text-xs text-gray-500">Contraseña generada automáticamente</div>
                <div className="flex items-center gap-2">
                  <code className="flex-1 rounded bg-white px-2 py-1 text-sm font-mono font-bold text-gray-800 border">
                    {generatedPassword}
                  </code>
                  <button type="button" onClick={() => navigator.clipboard?.writeText(generatedPassword)}
                    className="rounded p-1 text-gray-400 hover:text-gray-600" title="Copiar">
                    <Copy size={16} />
                  </button>
                  <button type="button" onClick={() => setGeneratedPassword(generatePassword())}
                    className="rounded p-1 text-gray-400 hover:text-gray-600" title="Regenerar">
                    <ArrowsClockwise size={16} />
                  </button>
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
              <div className="mb-1 text-xs text-gray-500">Nueva contraseña generada</div>
              <div className="flex items-center gap-2">
                <code className="flex-1 rounded bg-white px-2 py-1 text-sm font-mono font-bold text-gray-800 border">
                  {resetGeneratedPass}
                </code>
                <button type="button" onClick={() => navigator.clipboard?.writeText(resetGeneratedPass)}
                  className="rounded p-1 text-gray-400 hover:text-gray-600" title="Copiar">
                  <Copy size={16} />
                </button>
                <button type="button" onClick={() => setResetGeneratedPass(generatePassword())}
                  className="rounded p-1 text-gray-400 hover:text-gray-600" title="Regenerar">
                  <ArrowsClockwise size={16} />
                </button>
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
