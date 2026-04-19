/** Alinea con backend: múltiplos de 7 entre 7 y 364. */

export const MIN_PLAN_DAYS = 7
export const MAX_PLAN_DAYS = 364

/**
 * Valor inicial si aún no cargó GET /diets/duration-presets.
 * Debe coincidir con `QUICK_PLAN_DURATION_DAYS` en `app.logic.diet_duration`.
 */
export const FALLBACK_PLAN_DURATION_PRESETS: readonly number[] = [
  7, 14, 21, 28, 42, 56, 84, 112, 168, 364,
]

export function clampDurationDays(raw: string | number): number {
  const n = typeof raw === "string" ? Number(String(raw).replace(",", ".").trim()) : raw
  if (!Number.isFinite(n)) return MIN_PLAN_DAYS
  let v = Math.round(n / 7) * 7
  v = Math.max(MIN_PLAN_DAYS, Math.min(MAX_PLAN_DAYS, v))
  return v
}

/** Duración total guardada en el plan (si existe). */
export function planDurationDaysFromPlanJson(
  plan: Record<string, unknown> | null | undefined
): number | null {
  if (!plan || typeof plan !== "object") return null
  const d = plan.plan_duration_days
  return typeof d === "number" && Number.isFinite(d) && d > 0 ? d : null
}

/** Non-null when the typed number is rounded/clamped before send. */
export function durationAdjustHint(raw: string | number): string | null {
  const days = clampDurationDays(raw)
  const rawNum =
    typeof raw === "string" ? Number(String(raw).replace(",", ".").trim()) : raw
  if (!Number.isFinite(rawNum) || rawNum === days) return null
  return `Using ${days} days (adjusted from ${rawNum}; multiples of 7, max ${MAX_PLAN_DAYS}).`
}
