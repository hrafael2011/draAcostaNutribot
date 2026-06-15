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
  patient_id: number | null
  link_type: string
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
  link_type?: string | null
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
  role: string
  must_change_password: boolean
  is_active: boolean
  telegram_user_id?: string | null
  telegram_username?: string | null
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

export type DietGenerateRequest = {
  patient_id: number
  doctor_instruction?: string | null
  duration_days?: number
  meals_per_day?: 2 | 3 | 4 | 5
  strategy_mode?: DietStrategyMode
  diet_style?: string | null
  macro_mode?: { protein?: string; carbs?: string; fat?: string } | null
  manual_targets?: {
    daily_calories?: number
    protein_g?: number
    carbs_g?: number
    fat_g?: number
  } | null
}

export const NEXT_FEATURES = {
  batchDiets: false,
  advancedStrategies: false,  // Guided + Manual strategy modes (future feature)
  regenerate: false,           // Regenerate diet feature (future feature)
} as const;

// --- Wizard types ---

export type WizardStep =
  | "patient"
  | "note"
  | "duration"
  | "meals"
  | "strategy"
  | "guided_style"
  | "guided_macros"
  | "manual_targets"
  | "confirm"
  | "preview"

export const WIZARD_STEPS: { key: WizardStep; label: string }[] = [
  { key: "patient", label: "Paciente" },
  { key: "note", label: "Nota" },
  { key: "duration", label: "Duración" },
  { key: "meals", label: "Comidas" },
  { key: "strategy", label: "Modo" },
  { key: "confirm", label: "Confirmar" },
  { key: "preview", label: "Revisar" },
]

export type WizardState = {
  patientId: number | null
  patientName: string
  patientIds: number[]
  doctorInstruction: string
  durationDays: number
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
  generatedDiet: Diet | null
  isRegeneration: boolean
  parentDietId: number | null
}

export type WizardAction =
  | { type: "SET_FIELD"; field: string; value: unknown }
  | { type: "SET_DIET"; diet: Diet }
  | { type: "SET_PATIENT_IDS"; ids: number[] }
  | { type: "RESET" }

export function wizardReducer(state: WizardState, action: WizardAction): WizardState {
  if (action.type === "SET_FIELD") {
    return { ...state, [action.field]: action.value }
  }
  if (action.type === "SET_DIET") {
    return { ...state, generatedDiet: action.diet }
  }
  if (action.type === "SET_PATIENT_IDS") {
    return { ...state, patientIds: action.ids }
  }
  if (action.type === "RESET") {
    return { ...initialWizardState() }
  }
  return state
}

export function initialWizardState(patientId?: number): WizardState {
  return {
    patientId: patientId ?? null,
    patientName: "",
    patientIds: [],
    doctorInstruction: "",
    durationDays: 7,
    mealsPerDay: 4,
    strategyMode: "auto",
    dietStyle: "",
    macroProtein: "",
    macroCarbs: "",
    macroFat: "",
    manualKcal: "",
    manualProteinG: "",
    manualCarbsG: "",
    manualFatG: "",
    generatedDiet: null,
    isRegeneration: false,
    parentDietId: null,
  }
}

// ── Trash / Soft Delete ──────────────────────────────────────────────

export type TrashPatientItem = {
  id: number
  first_name: string
  last_name: string
  email: string | null
  deleted_at: string
}

export type TrashDietItem = {
  diet_id: number
  patient_id: number
  patient_name: string
  title: string | null
  deleted_at: string
}

export type PaginatedTrashPatients = {
  items: TrashPatientItem[]
  total: number
  page: number
  page_size: number
}

export type PaginatedTrashDiets = {
  items: TrashDietItem[]
  total: number
  page: number
  page_size: number
}
