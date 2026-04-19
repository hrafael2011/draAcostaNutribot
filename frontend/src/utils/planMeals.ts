import type { MealsPerDay } from "../types"

export const MEAL_PATTERNS: Record<MealsPerDay, string[]> = {
  2: ["breakfast", "dinner"],
  3: ["breakfast", "lunch", "dinner"],
  4: ["breakfast", "lunch", "snack", "dinner"],
  5: ["breakfast", "mid_morning_snack", "lunch", "snack", "dinner"],
}

export const MEAL_LABELS_ES: Record<string, string> = {
  breakfast: "Desayuno",
  mid_morning_snack: "Media mañana",
  lunch: "Almuerzo",
  snack: "Merienda",
  dinner: "Cena",
}

export function resolveMealSlots(plan: unknown): string[] {
  if (!plan || typeof plan !== "object") return [...MEAL_PATTERNS[4]]
  const p = plan as Record<string, unknown>
  const raw = p.meal_slots
  if (Array.isArray(raw)) {
    const slots = raw.filter((x): x is string => typeof x === "string" && x in MEAL_LABELS_ES)
    if (slots.length >= 2 && slots.length <= 5) return slots
  }
  const mpd = p.meals_per_day
  if (typeof mpd === "number" && mpd in MEAL_PATTERNS) {
    return [...MEAL_PATTERNS[mpd as MealsPerDay]]
  }
  return [...MEAL_PATTERNS[4]]
}

export function mealSlotsSummaryEs(slots: string[]): string {
  return slots.map((slot) => MEAL_LABELS_ES[slot] || slot).join(", ")
}
