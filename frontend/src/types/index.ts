export type Patient = {
  id: number
  doctor_id: number
  first_name: string
  last_name: string
  birth_date?: string | null
  sex?: string | null
  whatsapp?: string | null
  email?: string | null
  country?: string | null
  city?: string | null
  source: string
  is_active: boolean
  is_archived: boolean
}

export type PaginatedPatients = {
  items: Patient[]
  total: number
  page: number
  page_size: number
}

export type PatientProfile = {
  id: number
  patient_id: number
  objective?: string | null
  diseases?: string | null
  medications?: string | null
  food_allergies?: string | null
  foods_avoided?: string | null
  medical_history?: string | null
  dietary_style?: string | null
  food_preferences?: string | null
  disliked_foods?: string | null
  meal_schedule?: unknown
  water_intake_liters?: number | null
  activity_level?: string | null
  stress_level?: number | null
  sleep_quality?: number | null
  sleep_hours?: number | null
  budget_level?: string | null
  adherence_level?: number | null
  exercise_frequency_per_week?: number | null
  exercise_type?: string | null
  extra_notes?: string | null
  completed_by_patient: boolean
  completed_at?: string | null
}

export type PatientMetric = {
  id: number
  patient_id: number
  weight_kg?: number | null
  height_cm?: number | null
  neck_cm?: number | null
  chest_cm?: number | null
  waist_cm?: number | null
  hip_cm?: number | null
  leg_cm?: number | null
  calf_cm?: number | null
  recorded_at: string
  source: string
  notes?: string | null
  created_at: string
}

export type PatientSummary = {
  patient: { id: number; full_name: string }
  latest_metrics?: { weight_kg?: number | null; height_cm?: number | null } | null
  profile_flags: {
    has_allergies: boolean
    has_diseases: boolean
    is_profile_complete: boolean
  }
  latest_diet?: {
    id: number
    created_at: string
    plan_duration_days?: number | null
  } | null
}

export type DashboardSummary = {
  total_patients: number
  new_patients_30d: number
  incomplete_profiles: number
  diets_generated: number
  latest_activity: Record<string, unknown>[]
}

export type IntakeLink = {
  id: number
  doctor_id: number
  patient_id: number
  token: string
  status: string
  expires_at: string
  max_uses: number
  use_count: number
  last_used_at?: string | null
  created_at: string
}

export type IntakePublicMeta = {
  valid: boolean
  expires_at?: string | null
  patient_first_name?: string | null
  patient_last_name?: string | null
  message?: string | null
}

export type DoctorOut = {
  id: number
  full_name: string
  email: string
  phone?: string | null
  is_active: boolean
}

export type TelegramBindingState = {
  linked: boolean
  telegram_user_id?: string | null
  telegram_username?: string | null
  bot_username?: string | null
}

export type TelegramBindStart = {
  deep_link: string
  code: string
  expires_at: string
}

export type DietStrategyMode = "auto" | "guided" | "manual"
export type MealsPerDay = 2 | 3 | 4 | 5

/** Estado de formulario para modos de dieta (Fase 4 UI). */
export type DietStrategyFields = {
  mealsPerDay: MealsPerDay
  strategyMode: DietStrategyMode
  dietStyle: string
  macroProtein: string
  macroCarbs: string
  macroFat: string
  manualKcal: string
  manualProteinG: string
  manualCarbsG: string
  manualFatG: string
}

export type Diet = {
  id: number
  patient_id: number
  doctor_id: number
  status: string
  title?: string | null
  summary?: string | null
  structured_plan_json: Record<string, unknown>
  notes?: string | null
  created_at: string
  updated_at: string
}

export type DietVersion = {
  id: number
  diet_id: number
  version_number: number
  doctor_instruction?: string | null
  created_at: string
}

export type PaginatedDiets = {
  items: Diet[]
  total: number
  page: number
  page_size: number
}
