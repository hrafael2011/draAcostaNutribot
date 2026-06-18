import { useCallback, useEffect, useState } from "react"
import { MagnifyingGlass, Users, Plus } from "@phosphor-icons/react"
import { PatientRow } from "../components/patients/PatientRow"
import PatientDrawer from "../components/patients/PatientDrawer"
import { SkeletonRow } from "../components/ui/Skeleton"
import { EmptyState } from "../components/ui/EmptyState"
import { getPatients, getPatientSummary, softDeletePatient } from "../services/api"
import { useToast } from "../context/ToastContext"
import type { PaginatedPatients, Patient, PatientSummary } from "../types"

const STATUS_FILTERS = [
  { value: "", label: "Todos" },
  { value: "active_diet", label: "Con dieta activa" },
  { value: "incomplete_profile", label: "Perfil pendiente" },
  { value: "new_this_month", label: "Nuevos este mes" },
] as const

export default function Patients() {
  const { addToast } = useToast()

  const [data, setData] = useState<PaginatedPatients | null>(null)
  const [search, setSearch] = useState("")
  const [page, setPage] = useState(1)
  const [statusFilter, setStatusFilter] = useState("")
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [drawerOpen, setDrawerOpen] = useState(false)
  const [summaries, setSummaries] = useState<Record<number, PatientSummary | null>>({})

  // Debounced search: update debouncedSearch 300ms after the user stops typing
  const [debouncedSearch, setDebouncedSearch] = useState("")

  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(search)
      setPage(1)
    }, 300)
    return () => clearTimeout(timer)
  }, [search])

  const load = useCallback(() => {
    setLoading(true)
    setError(null)
    getPatients({
      search: debouncedSearch || undefined,
      status: statusFilter || undefined,
      page,
      page_size: 20,
    })
      .then(setData)
      .catch((e) => setError(e instanceof Error ? e.message : "Error"))
      .finally(() => setLoading(false))
  }, [debouncedSearch, page, statusFilter])

  useEffect(() => {
    load()
  }, [load])

  // Fetch summaries whenever the patient list changes
  useEffect(() => {
    if (!data?.items.length) return
    const ids = data.items.map((p) => p.id)
    Promise.all(
      ids.map((id) => getPatientSummary(id).catch(() => null)),
    ).then((results) => {
      const map: Record<number, PatientSummary | null> = {}
      ids.forEach((id, i) => {
        map[id] = results[i]
      })
      setSummaries(map)
    })
  }, [data?.items])

  const handleStatusChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setStatusFilter(e.target.value)
    setPage(1)
  }

  const handleDelete = async (patient: Patient) => {
    if (!window.confirm(`¿Eliminar a ${patient.first_name} ${patient.last_name}? Se moverá a la papelera.`)) return
    try {
      await softDeletePatient(patient.id)
      addToast("Paciente movido a la papelera", "success")
      load()
    } catch {
      addToast("Error al eliminar paciente", "error")
    }
  }

  const handleCreated = () => {
    addToast("Paciente creado exitosamente", "success")
    setDrawerOpen(false)
    setPage(1)
    load()
  }

  const totalPages = data ? Math.ceil(data.total / data.page_size) : 0

  return (
    <div className="px-4 py-6 max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-slate-800">Pacientes</h1>
        <button
          onClick={() => setDrawerOpen(true)}
          className="inline-flex items-center gap-2 rounded-full bg-emerald-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-emerald-700 active:scale-[0.97] transition-all"
        >
          <Plus size={18} weight="bold" />
          Nuevo Paciente
        </button>
      </div>

      {/* Search + Filters row */}
      <div className="flex flex-col sm:flex-row gap-3 mb-6">
        <div className="relative flex-1">
          <MagnifyingGlass
            className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none"
            size={18}
          />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Buscar pacientes..."
            className="w-full pl-10 pr-4 py-2.5 text-sm border border-slate-200 rounded-xl bg-white text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-colors"
          />
        </div>
        <select
          value={statusFilter}
          onChange={handleStatusChange}
          className="w-full sm:w-48 px-3.5 py-2.5 text-sm border border-slate-200 rounded-xl bg-white text-slate-700 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-colors appearance-none bg-[url('data:image/svg+xml;charset=utf-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20width%3D%2216%22%20height%3D%2216%22%20fill%3D%22%2394a3b8%22%3E%3Cpath%20d%3D%22M4.5%206l3.5%204%203.5-4%22%2F%3E%3C%2Fsvg%3E')] bg-[length:16px] bg-[right_12px_center] bg-no-repeat pr-9"
        >
          {STATUS_FILTERS.map((f) => (
            <option key={f.value} value={f.value}>
              {f.label}
            </option>
          ))}
        </select>
      </div>

      {/* Error state / no data */}
      {error && !data && (
        <div className="text-center py-16">
          <p className="text-red-600 text-sm mb-4">{error}</p>
          <button
            onClick={load}
            className="inline-flex items-center gap-2 rounded-full bg-red-50 px-5 py-2.5 text-sm font-semibold text-red-700 hover:bg-red-100 transition-colors"
          >
            Reintentar
          </button>
        </div>
      )}

      {/* Initial loading state */}
      {loading && !data && (
        <div className="bg-white rounded-2xl border border-slate-200 divide-y divide-slate-100">
          {Array.from({ length: 5 }).map((_, i) => (
            <SkeletonRow key={i} />
          ))}
        </div>
      )}

      {/* Empty state */}
      {!loading && data?.items.length === 0 && (
        <EmptyState
          icon={<Users size={48} />}
          title="Aún no hay pacientes"
          description="Crea tu primer paciente para comenzar"
          action={
            <button
              onClick={() => setDrawerOpen(true)}
              className="inline-flex items-center gap-2 rounded-full bg-emerald-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-emerald-700 active:scale-[0.97] transition-all"
            >
              <Plus size={18} weight="bold" />
              Crear primer paciente
            </button>
          }
        />
      )}

      {/* Patient list */}
      {data && data.items.length > 0 && (
        <>
          <div className="bg-white rounded-2xl border border-slate-200 divide-y divide-slate-100">
            {data.items.map((p) => (
              <PatientRow
                key={p.id}
                patient={p}
                summary={summaries[p.id]}
                onDelete={handleDelete}
              />
            ))}
          </div>

          {/* Pagination */}
          <div className="flex items-center justify-center gap-4 mt-6">
            <button
              disabled={page <= 1}
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              className="inline-flex items-center gap-1 rounded-full px-4 py-2 text-sm font-medium text-slate-600 hover:bg-slate-100 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            >
              &larr; Anterior
            </button>
            <span className="text-sm text-slate-500">
              P&aacute;gina {page} de {totalPages}
            </span>
            <button
              disabled={page >= totalPages}
              onClick={() => setPage((p) => p + 1)}
              className="inline-flex items-center gap-1 rounded-full px-4 py-2 text-sm font-medium text-slate-600 hover:bg-slate-100 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            >
              Siguiente &rarr;
            </button>
          </div>
        </>
      )}

      {/* Drawer */}
      <PatientDrawer
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        onCreated={handleCreated}
      />
    </div>
  )
}
