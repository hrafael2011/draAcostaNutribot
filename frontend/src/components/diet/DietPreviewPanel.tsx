import type { Diet } from "../../types"
import NutritionSummary from "./NutritionSummary"
import MealDayAccordion from "./MealDayAccordion"
import DietActions from "./DietActions"
import { useDietGeneration } from "../../hooks/useDietGeneration"

type Props = { diet: Diet }

export default function DietPreviewPanel({ diet }: Props) {
  const plan = diet.structured_plan_json
  const days = Array.isArray(plan.days) ? (plan.days as Record<string, unknown>[]) : []
  const mealSlots = Array.isArray(plan.meal_slots) ? (plan.meal_slots as string[]) : []
  const summary = typeof plan.summary === "string" ? plan.summary : diet.summary
  const { approve, discard, quickAdjust, regenerate } = useDietGeneration()

  const isPending = diet.status === "pending_approval"
  const loading = approve.isPending || discard.isPending || quickAdjust.isPending || regenerate.isPending

  return (
    <div className="space-y-4">
      {/* Title & Status */}
      <div>
        <h2 className="text-lg font-semibold text-gray-800">
          {diet.title || "Plan Nutricional"}
        </h2>
        <span className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium mt-1
          ${isPending ? "bg-amber-100 text-amber-700" : "bg-emerald-100 text-emerald-700"}`}>
          {isPending ? "Pendiente de aprobación" : "Aprobada"}
        </span>
      </div>

      {/* Summary text */}
      {summary && <p className="text-sm text-gray-600 whitespace-pre-wrap">{summary}</p>}

      {/* Nutrition engine */}
      <NutritionSummary diet={diet} />

      {/* Clinical rules */}
      {Array.isArray(plan.clinical_rules_applied) && plan.clinical_rules_applied.length > 0 && (
        <div className="rounded-lg border border-gray-200 p-3">
          <p className="text-xs font-semibold text-gray-600 mb-1">Reglas clínicas aplicadas:</p>
          {(plan.clinical_rules_applied as string[]).map((r, i) => (
            <p key={i} className="text-xs text-gray-500">• {r}</p>
          ))}
        </div>
      )}

      {/* Meal plan */}
      {days.length > 0 && <MealDayAccordion days={days} mealSlots={mealSlots} />}

      {/* Actions */}
      <DietActions
        dietId={diet.id}
        status={diet.status}
        onApprove={() => approve.mutate(diet.id)}
        onDiscard={() => discard.mutate(diet.id)}
        onRegenerate={() => {}}
        onQuickAdjust={(key, label) => quickAdjust.mutate({ dietId: diet.id, adjustment: label })}
        onDownloadPdf={() => {
          import("../../services/api").then(({ downloadDietPdf }) => downloadDietPdf(diet.id))
        }}
        loading={loading}
      />
    </div>
  )
}
