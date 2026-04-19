type Props = {
  presets: readonly number[]
  onSelect: (days: number) => void
}

export function DurationPresetButtons({ presets, onSelect }: Props) {
  return (
    <div style={{ marginBottom: 8 }}>
      <span style={{ fontSize: 12, color: "#666", display: "block", marginBottom: 6 }}>
        Quick (days)
      </span>
      <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
        {presets.map((d) => (
          <button
            key={d}
            type="button"
            onClick={() => onSelect(d)}
            style={{
              fontSize: 12,
              padding: "4px 8px",
              cursor: "pointer",
              border: "1px solid #ccc",
              borderRadius: 4,
              background: "#fafafa",
            }}
          >
            {d}
          </button>
        ))}
      </div>
    </div>
  )
}
