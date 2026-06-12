import { useEffect, useState } from "react"
import { Pencil } from "@phosphor-icons/react"

type Props = {
  label: string
  content: string
  editable?: boolean
  onSave?: (slotKey: string, newText: string) => void
  slotKey?: string
  dayIndex?: number
}

export default function MealCard({ label, content, editable, onSave, slotKey, dayIndex }: Props) {
  const [editing, setEditing] = useState(false)
  const [draft, setDraft] = useState(content)
  const [displayText, setDisplayText] = useState(content)

  // Sync when content prop changes from parent
  useEffect(() => {
    setDraft(content)
    setDisplayText(content)
  }, [content])

  const handleSave = () => {
    const newText = draft.trim()
    if (newText && newText !== content && onSave && slotKey !== undefined && dayIndex !== undefined) {
      // Optimistic update: show new text immediately
      setDisplayText(newText)
      onSave(slotKey, newText)
    }
    setEditing(false)
  }

  const handleCancel = () => {
    setDraft(displayText)
    setEditing(false)
  }

  if (editing) {
    return (
      <div className="rounded-lg border border-emerald-300 bg-emerald-50/30 px-3 py-2">
        <p className="text-xs font-semibold text-emerald-700 mb-1">{label}</p>
        <textarea
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          className="w-full text-sm text-gray-700 rounded-lg border border-slate-200 px-2 py-1 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 resize-y min-h-[60px]"
          autoFocus
          rows={2}
        />
        <div className="flex gap-1.5 mt-1.5">
          <button
            onClick={handleSave}
            className="px-2.5 py-1 text-xs font-medium rounded-full bg-emerald-600 text-white hover:bg-emerald-700 transition-colors"
          >
            Guardar
          </button>
          <button
            onClick={handleCancel}
            className="px-2.5 py-1 text-xs font-medium rounded-full border border-slate-200 text-slate-600 hover:bg-slate-50 transition-colors"
          >
            Cancelar
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className={`rounded-lg border border-gray-100 bg-white px-3 py-2 group ${editable ? "cursor-pointer hover:border-emerald-300 hover:bg-emerald-50/20 transition-colors" : ""}`}
      onClick={editable ? () => setEditing(true) : undefined}
    >
      <div className="flex items-start justify-between gap-2">
        <p className="text-xs font-semibold text-emerald-700">{label}</p>
        {editable && (
          <span className="shrink-0 text-gray-300 group-hover:text-emerald-500 transition-colors">
            <Pencil size={12} />
          </span>
        )}
      </div>
      <p className="mt-0.5 text-sm text-gray-700 whitespace-pre-wrap">{displayText}</p>
    </div>
  )
}
