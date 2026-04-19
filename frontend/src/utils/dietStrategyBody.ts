import type { DietStrategyFields } from "../types"

function optNum(raw: string): number | undefined {
  const t = raw.trim()
  if (!t) return undefined
  const n = Number(t)
  return Number.isFinite(n) && n > 0 ? n : undefined
}

/** Campos opcionales para POST /diets/generate y /diets/{id}/regenerate (modos nutricionales). */
export function buildDietStrategyBody(fields: DietStrategyFields): Record<string, unknown> {
  const out: Record<string, unknown> = {
    meals_per_day: fields.mealsPerDay,
    strategy_mode: fields.strategyMode,
  }
  if (fields.dietStyle.trim()) {
    out.diet_style = fields.dietStyle.trim()
  }
  const macro: Record<string, string> = {}
  if (fields.macroProtein) macro.protein = fields.macroProtein
  if (fields.macroCarbs) macro.carbs = fields.macroCarbs
  if (fields.macroFat) macro.fat = fields.macroFat
  if (Object.keys(macro).length) {
    out.macro_mode = macro
  }
  if (fields.strategyMode === "manual") {
    const mt: Record<string, number> = {}
    const kcal = optNum(fields.manualKcal)
    const pg = optNum(fields.manualProteinG)
    const cg = optNum(fields.manualCarbsG)
    const fg = optNum(fields.manualFatG)
    if (kcal != null) mt.daily_calories = kcal
    if (pg != null) mt.protein_g = pg
    if (cg != null) mt.carbs_g = cg
    if (fg != null) mt.fat_g = fg
    if (Object.keys(mt).length) {
      out.manual_targets = mt
    }
  }
  return out
}
