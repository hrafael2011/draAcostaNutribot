import { PencilSimple } from "@phosphor-icons/react"
import Button from "../ui/Button"
import QuickAdjustMenu from "./QuickAdjustMenu"
import { useState } from "react"

type Props = {
  dietId: number
  status: string
  onApprove: () => void
  onDiscard: () => void
  onQuickAdjust: (key: string, label: string) => void
  onDownloadPdf: () => void
  onToggleEdit?: () => void
  editing?: boolean
  loading: boolean
}

export default function DietActions({
  dietId,
  status,
  onApprove,
  onDiscard,
  onQuickAdjust,
  onDownloadPdf,
  onToggleEdit,
  editing,
  loading,
}: Props) {
  const [showQuickAdjust, setShowQuickAdjust] = useState(false)
  const isEditable = status === "pending_approval" || status === "generated"

  if (status === "pending_approval") {
    return (
      <div className="space-y-3">
        <div className="flex gap-2">
          <Button onClick={onApprove} disabled={loading} className="flex-1">
            ✅ Aprobar
          </Button>
          <Button variant="danger" onClick={onDiscard} disabled={loading} className="flex-1">
            🗑️ Descartar
          </Button>
        </div>
        <div className="space-y-2">
          <Button variant="ghost" onClick={() => setShowQuickAdjust(!showQuickAdjust)} className="w-full text-sm">
            ⚡ {showQuickAdjust ? "Ocultar ajustes" : "Ajuste rápido"}
          </Button>
          {showQuickAdjust && <QuickAdjustMenu onSelect={onQuickAdjust} loading={loading} />}
        </div>
        <Button variant="ghost" onClick={onToggleEdit} className="w-full text-sm">
          <span className="flex items-center justify-center gap-1.5">
            <PencilSimple size={14} />
            {editing ? "Dejar de editar" : "Editar comidas"}
          </span>
        </Button>
      </div>
    )
  }

  if (status === "generated") {
    return (
      <div className="space-y-2">
        <Button onClick={onDownloadPdf} className="w-full">
          📄 Descargar PDF
        </Button>
        <Button variant="ghost" onClick={onToggleEdit} className="w-full text-sm">
          <span className="flex items-center justify-center gap-1.5">
            <PencilSimple size={14} />
            {editing ? "Dejar de editar" : "Editar comidas"}
          </span>
        </Button>
      </div>
    )
  }

  return null
}
