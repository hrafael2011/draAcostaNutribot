import type {
  DashboardSummary,
  Diet,
  DietVersion,
  IntakeLink,
  IntakePublicMeta,
  PaginatedDiets,
  PaginatedPatients,
  Patient,
  PatientMetric,
  PatientProfile,
  PatientSummary,
  TelegramBindStart,
  TelegramBindingState,
  DietStrategyMode,
} from "../types"
import { notifyUnauthorized } from "./authBridge"

export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8001/api"

const TOKEN_KEY = "diet_admin_token"

export function getStoredToken(): string | null {
  return localStorage.getItem(TOKEN_KEY)
}

export function setStoredToken(token: string | null) {
  if (token) localStorage.setItem(TOKEN_KEY, token)
  else localStorage.removeItem(TOKEN_KEY)
}

export async function loginRequest(email: string, password: string) {
  const body = new URLSearchParams()
  body.set("username", email.trim())
  body.set("password", password)
  const res = await fetch(`${API_BASE_URL}/auth/token`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body,
  })
  if (!res.ok) {
    throw new Error(await readApiError(res) || "Login failed")
  }
  const data = (await res.json()) as {
    access_token: string
    role: string
    must_change_password: boolean
  }
  setStoredToken(data.access_token)
  return data
}

export async function changePasswordRequest(
  currentPassword: string,
  newPassword: string,
) {
  const res = await authFetch("/auth/change-password", {
    method: "POST",
    body: JSON.stringify({
      current_password: currentPassword,
      new_password: newPassword,
    }),
  })
  if (!res.ok) {
    throw new Error(await readApiError(res) || "Password change failed")
  }
  const data = (await res.json()) as {
    access_token: string
    role: string
    must_change_password: boolean
  }
  setStoredToken(data.access_token)
  return data
}

export async function fetchRegistrationOpen(): Promise<{ open: boolean }> {
  const res = await fetch(`${API_BASE_URL}/auth/registration-open`)
  if (!res.ok) {
    throw new Error(await readApiError(res) || "Request failed")
  }
  return res.json() as Promise<{ open: boolean }>
}

async function authFetch(path: string, init: RequestInit = {}) {
  const token = getStoredToken()
  const headers = new Headers(init.headers)
  if (token) headers.set("Authorization", `Bearer ${token}`)
  if (
    init.body &&
    !(init.body instanceof FormData) &&
    !headers.has("Content-Type")
  ) {
    headers.set("Content-Type", "application/json")
  }
  const res = await fetch(`${API_BASE_URL}${path}`, { ...init, headers })
  if (res.status === 401) {
    setStoredToken(null)
    notifyUnauthorized()
    throw new Error("UNAUTHORIZED")
  }
  return res
}

export async function readApiError(res: Response): Promise<string> {
  const t = await res.text()
  try {
    const j = JSON.parse(t) as { detail?: unknown }
    const d = j.detail
    if (typeof d === "string") return d
    if (d && typeof d === "object") {
      const o = d as Record<string, unknown>
      if (Array.isArray(o.reasons) && o.reasons.length)
        return o.reasons.map(String).join("\n")
      if (typeof o.message === "string") return o.message
    }
  } catch {
    /* use raw */
  }
  return t || res.statusText
}

export async function parseJson<T>(res: Response): Promise<T> {
  if (!res.ok) {
    throw new Error(await readApiError(res))
  }
  return res.json() as Promise<T>
}

export function getDashboard() {
  return authFetch("/dashboard/summary").then((r) =>
    parseJson<DashboardSummary>(r),
  )
}

export function getPatients(params: {
  search?: string
  status?: string
  page?: number
  page_size?: number
}) {
  const q = new URLSearchParams()
  if (params.search) q.set("search", params.search)
  if (params.status) q.set("status", params.status)
  if (params.page) q.set("page", String(params.page))
  if (params.page_size) q.set("page_size", String(params.page_size))
  const qs = q.toString()
  return authFetch(`/patients${qs ? `?${qs}` : ""}`).then((r) =>
    parseJson<PaginatedPatients>(r),
  )
}

export function createPatient(body: Partial<Patient> & Pick<Patient, "first_name" | "last_name">) {
  return authFetch("/patients", {
    method: "POST",
    body: JSON.stringify(body),
  }).then((r) => parseJson<Patient>(r))
}

export function getPatient(id: number) {
  return authFetch(`/patients/${id}`).then((r) => parseJson<Patient>(r))
}

export function patchPatient(id: number, body: Record<string, unknown>) {
  return authFetch(`/patients/${id}`, {
    method: "PATCH",
    body: JSON.stringify(body),
  }).then((r) => parseJson<Patient>(r))
}

export function getProfile(patientId: number) {
  return authFetch(`/patients/${patientId}/profile`).then(async (r) => {
    if (r.status === 404) return null
    return parseJson<PatientProfile>(r)
  })
}

export function patchProfile(patientId: number, body: Record<string, unknown>) {
  return authFetch(`/patients/${patientId}/profile`, {
    method: "PATCH",
    body: JSON.stringify(body),
  }).then((r) => parseJson<PatientProfile>(r))
}

export function getMetrics(patientId: number) {
  return authFetch(`/patients/${patientId}/metrics`).then((r) =>
    parseJson<PatientMetric[]>(r),
  )
}

export function addMetric(patientId: number, body: Record<string, unknown>) {
  return authFetch(`/patients/${patientId}/metrics`, {
    method: "POST",
    body: JSON.stringify(body),
  }).then((r) => parseJson<PatientMetric>(r))
}

export function getPatientSummary(patientId: number) {
  return authFetch(`/patients/${patientId}/summary`).then((r) =>
    parseJson<PatientSummary>(r),
  )
}

export function getIntakeLinks() {
  return authFetch("/intake-links").then((r) => parseJson<IntakeLink[]>(r))
}

export function createIntakeLink(body: {
  patient_id: number
  expires_in_days?: number
  max_uses?: number
}) {
  return authFetch("/intake-links", {
    method: "POST",
    body: JSON.stringify(body),
  }).then((r) => parseJson<IntakeLink>(r))
}

export function revokeIntakeLink(linkId: number) {
  return authFetch(`/intake-links/${linkId}/revoke`, { method: "POST" }).then(
    (r) => parseJson<IntakeLink>(r),
  )
}

export function validateIntakeToken(token: string) {
  return fetch(`${API_BASE_URL}/intake-links/public/${encodeURIComponent(token)}`).then(
    (r) => parseJson<IntakePublicMeta>(r),
  )
}

export function submitIntakeForm(token: string, body: Record<string, unknown>) {
  return fetch(
    `${API_BASE_URL}/intake-links/public/${encodeURIComponent(token)}/submit`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    },
  ).then(async (r) => {
    if (!r.ok) {
      throw new Error(await readApiError(r))
    }
    return r.json() as Promise<{ ok: boolean }>
  })
}

export function getDoctorMe() {
  return authFetch("/doctors/me").then((r) => parseJson(r))
}

export function getTelegramBinding() {
  return authFetch("/telegram/binding").then((r) =>
    parseJson<TelegramBindingState>(r),
  )
}

export function startTelegramBinding() {
  return authFetch("/telegram/binding/start", { method: "POST" }).then((r) =>
    parseJson<TelegramBindStart>(r),
  )
}

export function resetTelegramBinding() {
  return authFetch("/telegram/binding/reset", { method: "POST" }).then((r) =>
    parseJson<TelegramBindingState>(r),
  )
}

export function getPlanDurationPresets() {
  return authFetch("/diets/duration-presets").then((r) =>
    parseJson<{ days: number[] }>(r),
  ).then((body) => body.days)
}

export function getDiets(params: {
  patient_id?: number
  status?: string
  page?: number
  page_size?: number
}) {
  const q = new URLSearchParams()
  if (params.patient_id != null) q.set("patient_id", String(params.patient_id))
  if (params.status) q.set("status", params.status)
  if (params.page) q.set("page", String(params.page))
  if (params.page_size) q.set("page_size", String(params.page_size))
  const qs = q.toString()
  return authFetch(`/diets${qs ? `?${qs}` : ""}`).then((r) =>
    parseJson<PaginatedDiets>(r),
  )
}

export function getDiet(id: number) {
  return authFetch(`/diets/${id}`).then((r) => parseJson<Diet>(r))
}

export function getDietVersions(id: number) {
  return authFetch(`/diets/${id}/versions`).then((r) =>
    parseJson<DietVersion[]>(r),
  )
}

export function generateDiet(body: {
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
}) {
  return authFetch("/diets/generate", {
    method: "POST",
    body: JSON.stringify(body),
  }).then((r) => parseJson<Diet>(r))
}

export function regenerateDiet(
  id: number,
  body: {
    doctor_instruction?: string | null
    duration_days?: number | null
    meals_per_day?: 2 | 3 | 4 | 5 | null
    strategy_mode?: DietStrategyMode
    diet_style?: string | null
    macro_mode?: { protein?: string; carbs?: string; fat?: string } | null
    manual_targets?: {
      daily_calories?: number
      protein_g?: number
      carbs_g?: number
      fat_g?: number
    } | null
  },
) {
  return authFetch(`/diets/${id}/regenerate`, {
    method: "POST",
    body: JSON.stringify(body),
  }).then((r) => parseJson<Diet>(r))
}

export async function downloadDietPdf(id: number) {
  const token = getStoredToken()
  const res = await fetch(`${API_BASE_URL}/diets/${id}/pdf`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  })
  if (!res.ok) {
    throw new Error(await readApiError(res))
  }
  const blob = await res.blob()
  const url = URL.createObjectURL(blob)
  const a = document.createElement("a")
  a.href = url
  a.download = `diet-${id}.pdf`
  a.click()
  URL.revokeObjectURL(url)
}

export async function downloadDietExport(id: number, format: "txt" | "json") {
  const token = getStoredToken()
  const res = await fetch(
    `${API_BASE_URL}/diets/${id}/export?format=${format}`,
    {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    },
  )
  if (!res.ok) {
    throw new Error(await readApiError(res))
  }
  const blob = await res.blob()
  const url = URL.createObjectURL(blob)
  const a = document.createElement("a")
  a.href = url
  a.download = `diet-${id}.${format === "json" ? "json" : "txt"}`
  a.click()
  URL.revokeObjectURL(url)
}
