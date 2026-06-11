const STYLES = [
  { value: "", label: "Sin preferencia", desc: "El sistema elige" },
  { value: "balanced", label: "Equilibrada", desc: "Balance de macronutrientes" },
  { value: "low_carb", label: "Baja en carbohidratos", desc: "Reduce hidratos" },
  { value: "high_carb", label: "Alta en carbohidratos", desc: "Más energía de carbohidratos" },
  { value: "high_protein", label: "Alta en proteína", desc: "Prioriza proteína" },
  { value: "mediterranean", label: "Mediterránea", desc: "Verduras, legumbres, pescado, aceite de oliva" },
]

type Props = { value: string; onChange: (v: string) => void; onNext: () => void }

export default function DietStyleCards({ value, onChange, onNext }: Props) {
  return (
    <div className="space-y-3">
      <p className="text-sm font-medium text-gray-700">Elige un estilo de dieta</p>
      {STYLES.map((s) => (
        <button
          key={s.value}
          type="button"
          onClick={() => { onChange(s.value); if (s.value) onNext() }}
          className={`w-full rounded-lg border px-3 py-2 text-left transition-colors
            ${value === s.value
              ? "border-emerald-500 bg-emerald-50 shadow-sm"
              : "border-gray-200 bg-white hover:bg-gray-50"}`}
        >
          <span className="text-sm font-medium text-gray-800">{s.label}</span>
          <span className="ml-2 text-xs text-gray-400">{s.desc}</span>
        </button>
      ))}
    </div>
  )
}
