import { AnimatePresence, motion } from "framer-motion"
import { Check, PencilSimple } from "@phosphor-icons/react"

export interface ChangeItem {
  label: string
  oldValue?: string
  newValue: string
  isNew?: boolean
}

interface ConfirmModalProps {
  open: boolean
  title: string
  description?: string
  changes: ChangeItem[]
  onConfirm: () => void
  onEdit: () => void
  confirmLabel?: string
  editLabel?: string
  loading?: boolean
}

export default function ConfirmModal({
  open,
  title,
  description,
  changes,
  onConfirm,
  onEdit,
  confirmLabel = "Confirmar",
  editLabel = "Corregir",
  loading = false,
}: ConfirmModalProps) {
  return (
    <AnimatePresence>
      {open && (
        <motion.div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/20 backdrop-blur-sm"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
        >
          <motion.div
            className="w-full max-w-md mx-4 bg-white rounded-2xl shadow-xl"
            initial={{ opacity: 0, y: 16, scale: 0.96 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 16, scale: 0.96 }}
          >
            <div className="px-6 pt-6 pb-4">
              <h2 className="text-lg font-semibold text-gray-900">{title}</h2>
              {description && (
                <p className="text-sm text-gray-500 mt-1">{description}</p>
              )}
            </div>

            <div className="px-6 pb-4">
              <div className="rounded-xl bg-emerald-50 border border-emerald-200 p-4">
                {changes.length === 0 ? (
                  <p className="text-sm text-emerald-700 text-center">Sin cambios detectados</p>
                ) : (
                  <div className="space-y-2">
                    {changes.map((change, i) => (
                      <div key={i} className="flex justify-between items-center text-sm">
                        <span className="text-gray-500">{change.label}</span>
                        <div className="text-right">
                          {change.isNew ? (
                            <span className="font-medium text-emerald-700">{change.newValue}</span>
                          ) : (
                            <>
                              {change.oldValue && (
                                <span className="text-gray-400 line-through text-xs mr-1">
                                  {change.oldValue}
                                </span>
                              )}
                              <span className="font-medium text-gray-800">→ {change.newValue}</span>
                            </>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            <div className="px-6 pb-6 flex gap-3">
              <button
                type="button"
                onClick={onEdit}
                disabled={loading}
                className="flex-1 flex items-center justify-center gap-2 rounded-xl border border-gray-300 px-4 py-3 text-sm font-semibold text-gray-700 hover:bg-gray-50 disabled:opacity-50 transition-colors"
              >
                <PencilSimple size={18} />
                {editLabel}
              </button>
              <button
                type="button"
                onClick={onConfirm}
                disabled={loading || changes.length === 0}
                className="flex-1 flex items-center justify-center gap-2 rounded-xl bg-emerald-600 px-4 py-3 text-sm font-semibold text-white hover:bg-emerald-700 disabled:opacity-50 transition-colors"
              >
                <Check size={18} weight="bold" />
                {loading ? "Guardando..." : confirmLabel}
              </button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
