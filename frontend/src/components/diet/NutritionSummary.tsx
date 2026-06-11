import type { Diet } from "../../types"

type Props = { diet: Diet }

export default function NutritionSummary({ diet }: Props) {
  const plan = diet.structured_plan_json
  const engine = plan.nutrition_engine as Record<string, unknown> | undefined
  const macros = plan.macro_grams as Record<string, number> | undefined

  if (!engine && !macros) return null

  return (
    <div className="rounded-lg border border-gray-200 bg-gray-50 p-4">
      <h3 className="mb-2 text-sm font-semibold text-gray-700">📊 Resumen Nutricional</h3>
      <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-sm">
        {engine?.bmr != null && <p><span className="text-gray-500">TMB:</span> {String(engine.bmr)} kcal</p>}
        {engine?.tdee != null && <p><span className="text-gray-500">TDEE:</span> {String(engine.tdee)} kcal</p>}
        {engine?.goal_calories != null && <p><span className="text-gray-500">Objetivo:</span> {String(engine.goal_calories)} kcal</p>}
        {engine?.bmi != null && <p><span className="text-gray-500">BMI:</span> {String(engine.bmi)}</p>}
        {macros?.protein != null && <p><span className="text-gray-500">Proteína:</span> {String(macros.protein)}g</p>}
        {macros?.carbs != null && <p><span className="text-gray-500">Carbs:</span> {String(macros.carbs)}g</p>}
        {macros?.fat != null && <p><span className="text-gray-500">Grasas:</span> {String(macros.fat)}g</p>}
      </div>
      {Array.isArray(plan.alerts) && plan.alerts.length > 0 && (
        <div className="mt-2 space-y-1">
          {plan.alerts.map((a: unknown, i: number) => {
            const alert = a as { message_es?: string; blocks_generation?: boolean }
            return (
              <p key={i} className={`text-xs ${alert.blocks_generation ? "text-red-600" : "text-amber-600"}`}>
                ⚠️ {alert.message_es || String(a)}
              </p>
            )
          })}
        </div>
      )}
    </div>
  )
}
