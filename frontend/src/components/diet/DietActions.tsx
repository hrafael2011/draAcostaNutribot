import Button from "../ui/Button"
import QuickAdjustMenu from "./QuickAdjustMenu"
import { useState } from "react"

type Props = {
  dietId: number
  status: string
  onApprove: () => void
  onDiscard: () => void
  onRegenerate: () => void
  onQuickAdjust: (key: string, label: string) => void
  onDownloadPdf: () => void
  loading: boolean
}

export default function DietActions({
  dietId,
  status,
  onApprove,
  onDiscard,
  onRegenerate,
  onQuickAdjust,
  onDownloadPdf,
  loading,
}: Props) {
  const [showQuickAdjust, setShowQuickAdjust] = useState(false)

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
        <Button variant="ghost" onClick={onRegenerate} disabled={loading} className="w-full text-sm">
          🔄 Regenerar
        </Button>
      </div>
    )
  }

  if (status === "generated" || status === "approved") {
    return (
      <div className="space-y-2">
        <Button onClick={onDownloadPdf} className="w-full">
          📄 Descargar PDF
        </Button>
        <Button variant="ghost" onClick={onRegenerate} className="w-full text-sm">
          🔄 Regenerar (nueva versión)
        </Button>
      </div>
    )
  }

  return null
}
