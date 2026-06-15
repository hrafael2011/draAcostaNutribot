type Props = {
  presets: readonly number[]
  value?: number
  onSelect: (days: number) => void
}

export function DurationPresetButtons({ presets, value, onSelect }: Props) {
  return (
    <div className="mb-2">
      <span className="text-xs text-slate-500 block mb-1.5">
        Quick (days)
      </span>
      <div className="flex flex-wrap gap-2">
        {presets.map((d) => {
          const selected = value === d
          return (
            <button
              key={d}
              type="button"
              onClick={() => onSelect(d)}
              className={`rounded-lg border px-3 py-1 text-sm font-medium transition-colors ${
                selected
                  ? "border-emerald-500 bg-emerald-50 text-emerald-700 shadow-sm"
                  : "border-gray-200 bg-white text-gray-600 hover:bg-gray-50"
              }`}
            >
              {d}
            </button>
          )
        })}
      </div>
    </div>
  )
}
