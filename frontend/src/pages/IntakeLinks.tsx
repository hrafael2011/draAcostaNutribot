import { useEffect, useMemo, useState } from "react"
import { Link } from "react-router-dom"
import { LinkSimple, Plus, Copy, Trash, CaretDown } from "@phosphor-icons/react"
import { getIntakeLinks, getPatients, revokeIntakeLink } from "../services/api"
import { Avatar } from "../components/ui/Avatar"
import { Badge } from "../components/ui/Badge"
import { EmptyState } from "../components/ui/EmptyState"
import { SkeletonRow } from "../components/ui/Skeleton"
import ShareModal from "../components/sharing/ShareModal"
import { useToast } from "../context/ToastContext"
import type { IntakeLink, Patient } from "../types"

type BadgeVariant = "success" | "warning" | "danger" | "neutral" | "info"

export default function IntakeLinks() {
  const { addToast } = useToast()
  const [links, setLinks] = useState<IntakeLink[]>([])
  const [patients, setPatients] = useState<Patient[]>([])
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  // ShareModal state
  const [shareModalOpen, setShareModalOpen] = useState(false)
  const [sharePatientId, setSharePatientId] = useState<number>(0)
  const [sharePatientName, setSharePatientName] = useState("")
  const [shareLinkType, setShareLinkType] = useState<"register" | "update" | undefined>(undefined)

  // "New form" creation flow
  const [creating, setCreating] = useState(false)
  const [selectedPatientId, setSelectedPatientId] = useState<number | "">("")
  const [showFormDropdown, setShowFormDropdown] = useState(false)

  const patientById = useMemo(() => {
    const m = new Map<number, Patient>()
    patients.forEach((p) => m.set(p.id, p))
    return m
  }, [patients])

  async function refresh() {
    setError(null)
    const [ls, pg] = await Promise.all([
      getIntakeLinks(),
      getPatients({ page: 1, page_size: 100 }),
    ])
    setLinks(ls)
    setPatients(pg.items)
  }

  useEffect(() => {
    setLoading(true)
    refresh()
      .catch((e) => setError(e instanceof Error ? e.message : "Error"))
      .finally(() => setLoading(false))
  }, [])

  function publicUrl(token: string) {
    return `${window.location.origin}/intake/${encodeURIComponent(token)}`
  }

  function truncatedUrl(token: string) {
    const base = `${window.location.origin}/intake/`
    return `${base}${token.slice(0, 8)}...`
  }

  function getStatusBadge(status: string, useCount: number, maxUses: number): { label: string; variant: BadgeVariant } {
    if (status === "active" && useCount >= maxUses) {
      return { label: "Usado", variant: "info" }
    }
    switch (status) {
      case "active":
        return { label: "Activo", variant: "success" }
      case "completed":
        return { label: "Usado", variant: "info" }
      case "revoked":
        return { label: "Revocado", variant: "danger" }
      case "expired":
        return { label: "Expirado", variant: "neutral" }
      default:
        return { label: status, variant: "neutral" }
    }
  }

  function formatDate(dateStr: string) {
    return new Date(dateStr).toLocaleDateString("es-MX", {
      year: "numeric",
      month: "short",
      day: "numeric",
    })
  }

  function handleStartCreate() {
    setSelectedPatientId("")
    setCreating(true)
  }

  function handleCreateRegisterLink() {
    setSharePatientId(0)
    setSharePatientName("")
    setShareLinkType("register")
    setShareModalOpen(true)
  }

  function handleCancelCreate() {
    setCreating(false)
    setSelectedPatientId("")
  }

  function handleConfirmCreate() {
    if (selectedPatientId === "") return
    const p = patientById.get(Number(selectedPatientId))
    if (!p) return
    setSharePatientId(p.id)
    setSharePatientName(`${p.first_name} ${p.last_name}`)
    setShareLinkType("update")
    setCreating(false)
    setSelectedPatientId("")
    setShareModalOpen(true)
  }

  function handleShareModalClose() {
    setShareModalOpen(false)
    setSharePatientId(0)
    setSharePatientName("")
    setShareLinkType(undefined)
    refresh().catch((e) => setError(e instanceof Error ? e.message : "Error"))
  }

  async function handleRevoke(id: number) {
    try {
      await revokeIntakeLink(id)
      addToast("Formulario revocado", "success")
      await refresh()
    } catch (err) {
      addToast(err instanceof Error ? err.message : "Error al revocar", "error")
    }
  }

  async function handleCopy(text: string) {
    try {
      await navigator.clipboard.writeText(text)
      addToast("Copiado al portapapeles", "success")
    } catch {
      addToast("No se pudo copiar", "error")
    }
  }

  // ---- Loading state ----
  if (loading) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8">
        <div className="flex items-center justify-between mb-8">
          <div className="h-8 w-48 bg-slate-200 rounded-lg animate-pulse" />
          <div className="h-10 w-40 bg-slate-200 rounded-full animate-pulse" />
        </div>
        <div className="space-y-3">
          <SkeletonRow />
          <SkeletonRow />
          <SkeletonRow />
          <SkeletonRow />
        </div>
      </div>
    )
  }

  // ---- Error state ----
  if (error && links.length === 0) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8">
        <div className="flex items-center justify-between mb-8">
          <h1 className="text-2xl font-bold text-slate-800">Formularios</h1>
        </div>
        <div className="rounded-2xl bg-red-50 border border-red-200 px-5 py-4 flex items-center justify-between">
          <p className="text-sm text-red-700">{error}</p>
          <button
            type="button"
            onClick={() => {
              setError(null)
              setLoading(true)
              refresh()
                .catch((e) => setError(e instanceof Error ? e.message : "Error"))
                .finally(() => setLoading(false))
            }}
            className="text-sm font-medium text-red-600 hover:text-red-700 underline shrink-0 ml-4"
          >
            Reintentar
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      {/* Page header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
        <div className="flex items-center gap-3">
          <span className="rounded-xl bg-emerald-100 text-emerald-700 p-2.5">
            <LinkSimple size={24} weight="duotone" />
          </span>
          <div>
            <h1 className="text-2xl font-bold text-slate-800">Formularios</h1>
            <p className="text-sm text-slate-500 mt-0.5">
              Comparte enlaces para que tus pacientes llenen su informacion sin necesidad de iniciar sesion
            </p>
          </div>
        </div>
        <div className="relative">
          <button
            type="button"
            onClick={() => setShowFormDropdown(!showFormDropdown)}
            className="flex items-center gap-2 rounded-full bg-emerald-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-emerald-700 transition-colors shadow-sm"
          >
            <Plus size={18} weight="bold" />
            Nuevo Formulario
            <CaretDown size={14} weight="bold" className={`transition-transform ${showFormDropdown ? "rotate-180" : ""}`} />
          </button>

          {showFormDropdown && (
            <>
              <div className="fixed inset-0 z-40" onClick={() => setShowFormDropdown(false)} />
              <div className="absolute right-0 sm:left-0 top-full mt-2 z-50 w-64 sm:w-72 bg-white rounded-2xl shadow-xl border border-slate-200 py-2 overflow-hidden">
                <button
                  type="button"
                  onClick={() => { setShowFormDropdown(false); handleCreateRegisterLink(); }}
                  className="flex items-start gap-3 w-full px-4 py-3 text-left hover:bg-emerald-50 transition-colors"
                >
                  <span className="text-xl mt-0.5">📝</span>
                  <div>
                    <p className="text-sm font-semibold text-slate-800">Registro</p>
                    <p className="text-xs text-slate-500">Para paciente nuevo — se crea automáticamente</p>
                  </div>
                </button>
                <div className="border-t border-slate-100" />
                <button
                  type="button"
                  disabled={patients.length === 0}
                  onClick={() => { setShowFormDropdown(false); handleStartCreate(); }}
                  className={`flex items-start gap-3 w-full px-4 py-3 text-left transition-colors ${
                    patients.length === 0
                      ? "opacity-50 cursor-not-allowed"
                      : "hover:bg-emerald-50"
                  }`}
                  title={patients.length === 0 ? "No hay pacientes registrados" : undefined}
                >
                  <span className="text-xl mt-0.5">🔄</span>
                  <div>
                    <p className="text-sm font-semibold text-slate-800">Actualización</p>
                    <p className="text-xs text-slate-500">
                      {patients.length === 0
                        ? "No hay pacientes registrados aún"
                        : "Para paciente existente — elige quién"}
                    </p>
                  </div>
                </button>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Patient selector for new form */}
      {creating && (
        <div className="mb-8 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <h3 className="text-sm font-semibold text-slate-700 mb-3">Seleccionar paciente</h3>
          <div className="flex flex-col sm:flex-row sm:items-end gap-3">
            <div className="flex-1">
              <label htmlFor="new-form-patient" className="block text-xs font-medium text-slate-500 mb-1.5">
                Paciente
              </label>
              <select
                id="new-form-patient"
                required
                value={selectedPatientId}
                onChange={(e) =>
                  setSelectedPatientId(e.target.value === "" ? "" : Number(e.target.value))
                }
                className="w-full rounded-xl border border-slate-300 px-3 py-2.5 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent bg-white"
              >
                <option value="">Seleccionar...</option>
                {patients.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.first_name} {p.last_name}
                  </option>
                ))}
              </select>
            </div>
            <button
              type="button"
              onClick={handleConfirmCreate}
              disabled={selectedPatientId === ""}
              className="w-full sm:w-auto rounded-full bg-emerald-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-emerald-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              Continuar
            </button>
            <button
              type="button"
              onClick={handleCancelCreate}
              className="w-full sm:w-auto rounded-full border border-slate-300 px-4 py-2.5 text-sm font-medium text-slate-600 hover:bg-slate-50 transition-colors"
            >
              Cancelar
            </button>
          </div>
        </div>
      )}

      {/* Error banner (when we have existing data) */}
      {error && links.length > 0 && (
        <div className="mb-6 rounded-2xl bg-red-50 border border-red-200 px-5 py-4 flex items-center justify-between">
          <p className="text-sm text-red-700">{error}</p>
          <button
            type="button"
            onClick={() => {
              setError(null)
              refresh().catch((e) => setError(e instanceof Error ? e.message : "Error"))
            }}
            className="text-sm font-medium text-red-600 hover:text-red-700 underline shrink-0 ml-4"
          >
            Reintentar
          </button>
        </div>
      )}

      {/* Empty state */}
      {!loading && links.length === 0 && !error && (
        <EmptyState
          icon={<LinkSimple size={48} />}
          title="Aún no has creado formularios"
          description="Crea un formulario para que tu paciente pueda completar su información nutricional."
          action={
            <button
              type="button"
              onClick={handleStartCreate}
              className="flex items-center gap-2 rounded-full bg-emerald-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-emerald-700 transition-colors shadow-sm"
            >
              <Plus size={18} weight="bold" />
              Crear primer formulario
            </button>
          }
        />
      )}

      {/* Link cards */}
      {links.length > 0 && (
        <div className="space-y-3">
          {links.map((link) => {
            const p = link.patient_id ? patientById.get(link.patient_id) : undefined
            const name = p ? `${p.first_name} ${p.last_name}` : link.patient_id ? `#${link.patient_id}` : "Nuevo paciente"
            const url = publicUrl(link.token)
            const badge = getStatusBadge(link.status, link.use_count, link.max_uses)
            const isActive = link.status === "active"

            return (
              <div
                key={link.id}
                className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm hover:shadow-md transition-shadow"
              >
                <div className="flex flex-col sm:flex-row sm:items-start justify-between mb-4 gap-3">
                  <div className="flex items-center gap-3 min-w-0">
                    <Avatar firstName={p?.first_name} lastName={p?.last_name} size="md" />
                    <div className="min-w-0">
                      {p ? (
                        <Link
                          to={`/patients/${p.id}`}
                          className="text-sm font-semibold text-slate-800 hover:text-emerald-600 transition-colors truncate block"
                        >
                          {name}
                        </Link>
                      ) : (
                        <span className="text-sm font-semibold text-slate-500">{name}</span>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-2 flex-wrap">
                    <Badge variant={badge.variant}>{badge.label}</Badge>
                    <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${
                      link.link_type === "register"
                        ? "bg-emerald-50 text-emerald-700"
                        : "bg-blue-50 text-blue-700"
                    }`}>
                      {link.link_type === "register" ? "📝 Registro" : "🔄 Actualización"}
                    </span>
                    <span className="text-xs text-slate-400">
                      {link.use_count}/{link.max_uses} usos
                    </span>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4 mb-4">
                  <div>
                    <span className="text-xs text-slate-400 block">Creado</span>
                    <span className="text-sm text-slate-700">{formatDate(link.created_at)}</span>
                  </div>
                  <div>
                    <span className="text-xs text-slate-400 block">Expira</span>
                    <span className="text-sm text-slate-700">{formatDate(link.expires_at)}</span>
                  </div>
                </div>

                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-3 border-t border-slate-100">
                  <div className="flex items-center gap-2 min-w-0 flex-1">
                    <span className="text-xs text-slate-400 truncate font-mono">
                      {truncatedUrl(link.token)}
                    </span>
                    <button
                      type="button"
                      onClick={() => handleCopy(url)}
                      className="shrink-0 flex items-center gap-1 rounded-lg px-2.5 py-1.5 text-xs font-medium text-slate-500 hover:bg-slate-100 transition-colors"
                      title="Copiar enlace"
                    >
                      <Copy size={14} />
                      Copiar
                    </button>
                  </div>
                  {isActive && (
                    <button
                      type="button"
                      onClick={() => handleRevoke(link.id)}
                      className="shrink-0 flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-medium text-red-600 hover:bg-red-50 transition-colors"
                    >
                      <Trash size={14} />
                      Revocar
                    </button>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      )}

      {/* ShareModal */}
      {shareModalOpen && (
        <ShareModal
          open={shareModalOpen}
          onClose={handleShareModalClose}
          patientId={sharePatientId > 0 ? sharePatientId : undefined}
          patientName={sharePatientName || undefined}
          initialLinkType={shareLinkType}
        />
      )}
    </div>
  )
}
