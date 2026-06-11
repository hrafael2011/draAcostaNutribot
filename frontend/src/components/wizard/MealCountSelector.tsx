import type { MealsPerDay } from "../../types"

const OPTIONS: { value: MealsPerDay; label: string; meals: string }[] = [
  { value: 2, label: "2 comidas", meals: "Desayuno, Cena" },
  { value: 3, label: "3 comidas", meals: "Desayuno, Almuerzo, Cena" },
  { value: 4, label: "4 comidas", meals: "Desayuno, Almuerzo, Merienda, Cena" },
  { value: 5, label: "5 comidas", meals: "Desayuno, Snack, Almuerzo, Merienda, Cena" },
]

type Props = { value: MealsPerDay; onChange: (v: MealsPerDay) => void }

export default function MealCountSelector({ value, onChange }: Props) {
  return (
    <div className="space-y-4">
      <p className="text-sm font-medium text-gray-700">¿Cuántas comidas por día?</p>
      <div className="space-y-2">
        {OPTIONS.map((opt) => (
          <button
            key={opt.value}
            type="button"
            onClick={() => onChange(opt.value)}
            className={`w-full rounded-lg border px-4 py-3 text-left transition-colors
              ${value === opt.value
                ? "border-emerald-500 bg-emerald-50 shadow-sm"
                : "border-gray-200 bg-white hover:bg-gray-50"}`}
          >
            <span className="text-sm font-medium text-gray-800">{opt.label}</span>
            <span className="ml-2 text-xs text-gray-400">{opt.meals}</span>
          </button>
        ))}
      </div>
    </div>
  )
}
