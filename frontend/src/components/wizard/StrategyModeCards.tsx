import type { DietStrategyMode } from "../../types"

const MODES: { value: DietStrategyMode; title: string; desc: string }[] = [
  { value: "auto", title: "Automático", desc: "El sistema calcula todo basado en los datos del paciente" },
  { value: "guided", title: "Guiado", desc: "Tú eliges estilo de dieta y preferencias de macronutrientes" },
  { value: "manual", title: "Manual", desc: "Tú defines objetivos exactos de calorías y macronutrientes" },
]

type Props = { value: DietStrategyMode; onChange: (v: DietStrategyMode) => void }

export default function StrategyModeCards({ value, onChange }: Props) {
  return (
    <div className="space-y-3">
      <p className="text-sm font-medium text-gray-700">¿Cómo quieres calcular los objetivos nutricionales?</p>
      {MODES.map((m) => (
        <button
          key={m.value}
          type="button"
          onClick={() => onChange(m.value)}
          className={`w-full rounded-xl border p-4 text-left transition-colors
            ${value === m.value
              ? "border-emerald-500 bg-emerald-50 shadow-md ring-1 ring-emerald-500"
              : "border-gray-200 bg-white shadow-sm hover:shadow-md"}`}
        >
          <p className="font-semibold text-gray-800">{m.title}</p>
          <p className="text-sm text-gray-500">{m.desc}</p>
        </button>
      ))}
    </div>
  )
}
