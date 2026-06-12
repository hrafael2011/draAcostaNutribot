import Accordion from "../ui/Accordion"
import MealCard from "./MealCard"

type Props = {
  days: Record<string, unknown>[]
  mealSlots: string[]
  editable?: boolean
  onMealSave?: (dayIndex: number, slotKey: string, text: string) => void
}

const SLOT_LABELS_ES: Record<string, string> = {
  breakfast: "🥐 Desayuno",
  mid_morning_snack: "🍌 Media Mañana",
  lunch: "🥗 Almuerzo",
  snack: "🍎 Merienda",
  dinner: "🍽️ Cena",
}

export default function MealDayAccordion({ days, mealSlots, editable, onMealSave }: Props) {
  return (
    <div className="space-y-2">
      <h3 className="text-sm font-semibold text-gray-700">📅 Plan de Comidas</h3>
      {days.map((day, i) => {
        const meals = (day.meals || day) as Record<string, string>
        return (
          <Accordion key={i} title={`Día ${i + 1}`} defaultOpen={i === 0}>
            <div className="space-y-2">
              {mealSlots.map((slot) => {
                const text = meals[slot]
                if (!text) return null
                return (
                  <MealCard
                    key={slot}
                    label={SLOT_LABELS_ES[slot] || slot}
                    content={text}
                    slotKey={slot}
                    dayIndex={i}
                    editable={editable}
                    onSave={onMealSave ? (key, txt) => onMealSave(i, key, txt) : undefined}
                  />
                )
              })}
            </div>
          </Accordion>
        )
      })}
    </div>
  )
}
