import { useState, useEffect, useCallback } from "react"
import { Trash, ArrowClockwise, WarningCircle } from "@phosphor-icons/react"
import { getTrashPatients, getTrashDiets, restorePatient, hardDeletePatient, restoreDiet, hardDeleteDiet } from "../services/api"
import { useToast } from "../context/ToastContext"
import type { TrashPatientItem, TrashDietItem } from "../types"

type Tab = "patients" | "diets"

function ConfirmDialog({ open, title, message, onConfirm, onCancel }: {
  open: boolean
  title: string
  message: string
  onConfirm: () => void
  onCancel: () => void
}) {
  if (!open) return null
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/20 backdrop-blur-sm" onClick={onCancel}>
      <div className="bg-white rounded-2xl shadow-xl max-w-sm mx-4 p-6" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 rounded-full bg-red-100 flex items-center justify-center shrink-0">
            <WarningCircle size={24} className="text-red-600" />
          </div>
          <h3 className="text-lg font-semibold text-slate-800">{title}</h3>
        </div>
        <p className="text-sm text-slate-600 mb-6">{message}</p>
        <div className="flex gap-3">
          <button onClick={onCancel} className="flex-1 px-4 py-2.5 rounded-xl text-sm font-medium bg-white border border-slate-200 text-slate-700 hover:bg-slate-50 transition-colors">
            Cancelar
          </button>
          <button onClick={onConfirm} className="flex-1 px-4 py-2.5 rounded-xl text-sm font-medium bg-red-600 text-white hover:bg-red-700 transition-colors">
            Eliminar
          </button>
        </div>
      </div>
    </div>
  )
}

export default function TrashPage() {
  const { addToast } = useToast()
  const [tab, setTab] = useState<Tab>("patients")
  const [search, setSearch] = useState("")
  const [patients, setPatients] = useState<TrashPatientItem[]>([])
  const [diets, setDiets] = useState<TrashDietItem[]>([])
  const [loading, setLoading] = useState(true)
  const [confirmDelete, setConfirmDelete] = useState<{ type: Tab; id: number; name: string } | null>(null)

  const fetchPatients = useCallback(async () => {
    try {
      const data = await getTrashPatients(search || undefined)
      setPatients(data.items)
    } catch {
      addToast("Error al cargar pacientes eliminados", "error")
    }
  }, [search, addToast])

  const fetchDiets = useCallback(async () => {
    try {
      const data = await getTrashDiets(search || undefined)
      setDiets(data.items)
    } catch {
      addToast("Error al cargar dietas eliminadas", "error")
    }
  }, [search, addToast])

  useEffect(() => {
    setLoading(true)
    Promise.all([fetchPatients(), fetchDiets()]).finally(() => setLoading(false))
  }, [fetchPatients, fetchDiets])

  const handleRestore = async (type: Tab, id: number) => {
    try {
      if (type === "patients") {
        await restorePatient(id)
        addToast("Paciente restaurado exitosamente", "success")
      } else {
        await restoreDiet(id)
        addToast("Dieta restaurada exitosamente", "success")
      }
      if (type === "patients") fetchPatients()
      else fetchDiets()
    } catch (err) {
      addToast(err instanceof Error ? err.message : "Error al restaurar", "error")
    }
  }

  const handleHardDelete = async () => {
    if (!confirmDelete) return
    const { type, id } = confirmDelete
    try {
      if (type === "patients") {
        await hardDeletePatient(id)
        addToast("Paciente eliminado permanentemente", "success")
      } else {
        await hardDeleteDiet(id)
        addToast("Dieta eliminada permanentemente", "success")
      }
      if (type === "patients") fetchPatients()
      else fetchDiets()
    } catch {
      addToast("Error al eliminar permanentemente", "error")
    } finally {
      setConfirmDelete(null)
    }
  }

  return (
    <div>
      <h1 className="text-2xl font-bold text-slate-800 mb-6">🗑️ Papelera</h1>

      {/* Tabs */}
      <div className="flex gap-0 border-b border-slate-200 mb-6">
        <button
          onClick={() => setTab("patients")}
          className={`px-5 py-3 text-sm font-medium border-b-2 transition-colors ${
            tab === "patients"
              ? "border-emerald-500 text-emerald-700"
              : "border-transparent text-slate-500 hover:text-slate-700"
          }`}
        >
          🧑 Pacientes ({patients.length})
        </button>
        <button
          onClick={() => setTab("diets")}
          className={`px-5 py-3 text-sm font-medium border-b-2 transition-colors ${
            tab === "diets"
              ? "border-emerald-500 text-emerald-700"
              : "border-transparent text-slate-500 hover:text-slate-700"
          }`}
        >
          📋 Dietas ({diets.length})
        </button>
      </div>

      {/* Search */}
      <div className="mb-4">
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Buscar en papelera..."
          className="w-full max-w-xs px-3.5 py-2.5 text-sm border border-slate-200 rounded-xl bg-white text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-colors"
        />
      </div>

      {/* Content */}
      {loading ? (
        <div className="text-center py-12 text-sm text-slate-400">Cargando...</div>
      ) : tab === "patients" ? (
        patients.length === 0 ? (
          <div className="text-center py-12 text-sm text-slate-400">No hay pacientes en la papelera</div>
        ) : (
          <div className="border border-slate-200 rounded-xl overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200">
                  <th className="text-left px-4 py-3 font-semibold text-slate-600">Paciente</th>
                  <th className="text-left px-4 py-3 font-semibold text-slate-600">Eliminado</th>
                  <th className="text-right px-4 py-3 font-semibold text-slate-600">Acciones</th>
                </tr>
              </thead>
              <tbody>
                {patients.map((p) => (
                  <tr key={p.id} className="border-b border-slate-100 hover:bg-slate-50">
                    <td className="px-4 py-3">
                      <div className="font-medium text-slate-800">{p.first_name} {p.last_name}</div>
                      {p.email && <div className="text-xs text-slate-400">{p.email}</div>}
                    </td>
                    <td className="px-4 py-3 text-slate-500">
                      {new Date(p.deleted_at).toLocaleDateString("es-ES", { day: "2-digit", month: "2-digit", year: "numeric" })}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <div className="flex gap-2 justify-end">
                        <button
                          onClick={() => handleRestore("patients", p.id)}
                          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-emerald-50 text-emerald-700 hover:bg-emerald-100 transition-colors"
                        >
                          <ArrowClockwise size={14} /> Restaurar
                        </button>
                        <button
                          onClick={() => setConfirmDelete({ type: "patients", id: p.id, name: `${p.first_name} ${p.last_name}` })}
                          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-red-50 text-red-600 hover:bg-red-100 transition-colors"
                        >
                          <Trash size={14} /> Eliminar
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )
      ) : (
        diets.length === 0 ? (
          <div className="text-center py-12 text-sm text-slate-400">No hay dietas en la papelera</div>
        ) : (
          <div className="border border-slate-200 rounded-xl overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200">
                  <th className="text-left px-4 py-3 font-semibold text-slate-600">Paciente</th>
                  <th className="text-left px-4 py-3 font-semibold text-slate-600">Título</th>
                  <th className="text-left px-4 py-3 font-semibold text-slate-600">Eliminado</th>
                  <th className="text-right px-4 py-3 font-semibold text-slate-600">Acciones</th>
                </tr>
              </thead>
              <tbody>
                {diets.map((d) => (
                  <tr key={d.diet_id} className="border-b border-slate-100 hover:bg-slate-50">
                    <td className="px-4 py-3 font-medium text-slate-800">{d.patient_name}</td>
                    <td className="px-4 py-3 text-slate-500">{d.title || "—"}</td>
                    <td className="px-4 py-3 text-slate-500">
                      {new Date(d.deleted_at).toLocaleDateString("es-ES", { day: "2-digit", month: "2-digit", year: "numeric" })}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <div className="flex gap-2 justify-end">
                        <button
                          onClick={() => handleRestore("diets", d.diet_id)}
                          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-emerald-50 text-emerald-700 hover:bg-emerald-100 transition-colors"
                        >
                          <ArrowClockwise size={14} /> Restaurar
                        </button>
                        <button
                          onClick={() => setConfirmDelete({ type: "diets", id: d.diet_id, name: `dieta de ${d.patient_name}` })}
                          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-red-50 text-red-600 hover:bg-red-100 transition-colors"
                        >
                          <Trash size={14} /> Eliminar
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )
      )}

      {/* Hint */}
      <p className="mt-4 text-xs text-slate-400 text-center">
        Los elementos eliminados se quedan aquí hasta que los restaures o los elimines permanentemente.
      </p>

      {/* Confirm dialog */}
      <ConfirmDialog
        open={confirmDelete !== null}
        title="¿Eliminar permanentemente?"
        message={`Esta acción no se puede deshacer. Se eliminará ${confirmDelete?.name || ""} de forma permanente.`}
        onConfirm={handleHardDelete}
        onCancel={() => setConfirmDelete(null)}
      />
    </div>
  )
}
