import type { Diet } from "../../types"

type Props = { diet: Diet }

export default function NutritionSummary({ diet }: Props) {
  const plan = diet.structured_plan_json
  const engine = plan.nutrition_engine as Record<string, unknown> | undefined
  const macros = plan.macro_grams as Record<string, number> | undefined
  const dailyCals = (plan.daily_calories as number) ?? engine?.goal_calories

  // Support both key formats: original uses protein_g/carbs_g/fat_g, recalculation uses protein/carbs/fat
  const protein = macros?.protein ?? macros?.protein_g
  const carbs = macros?.carbs ?? macros?.carbs_g
  const fat = macros?.fat ?? macros?.fat_g

  if (!engine && !macros && !dailyCals) return null

  return (
    <div className="rounded-lg border border-gray-200 bg-gray-50 p-4">
      <h3 className="mb-2 text-sm font-semibold text-gray-700">📊 Resumen Nutricional</h3>
      <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-sm">
        {dailyCals != null && <p><span className="text-gray-500">Calorías:</span> {String(dailyCals)} kcal</p>}
        {engine?.bmr != null && <p><span className="text-gray-500">TMB:</span> {String(engine.bmr)} kcal</p>}
        {engine?.tdee != null && <p><span className="text-gray-500">TDEE:</span> {String(engine.tdee)} kcal</p>}
        {engine?.bmi != null && <p><span className="text-gray-500">IMC:</span> {String(engine.bmi)}</p>}
        {protein != null && <p><span className="text-gray-500">Proteína:</span> {String(protein)} g</p>}
        {carbs != null && <p><span className="text-gray-500">Carbohidratos:</span> {String(carbs)} g</p>}
        {fat != null && <p><span className="text-gray-500">Grasas:</span> {String(fat)} g</p>}
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
