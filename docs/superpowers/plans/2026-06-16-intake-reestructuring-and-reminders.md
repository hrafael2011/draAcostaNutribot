# Reestructuración Intake + Recordatorios — Plan de Implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Separar el formulario de intake público en dos momentos (paciente vs doctor) e integrar con recordatorios automáticos a los 30 días.

**Architecture:** El paciente llena solo 10 campos en el formulario público (sin clínica ni medidas). El doctor completa 26 campos en el panel de administración. Los 30 días el scheduler envía email si hay correo, o la doctora pregunta presencialmente si no.

**Tech Stack:** FastAPI, SQLAlchemy, React + Tailwind, REST Countries API + CountryStateCity API

**Spec:** `docs/superpowers/specs/2026-06-16-intake-reestructuring-and-reminders.md`

---

### Task 1: Backend schemas — limpiar IntakePublicSubmit

**Files:**
- Modify: `backend/app/schemas.py:261-298`

Quitar del schema de registro todos los campos clínicos y medidas corporales. Dejar solo datos personales + disliked_foods.

- [ ] **Step 1: Reemplazar IntakePublicSubmit**

Cambiar de los ~20 campos actuales a solo estos:

```python
class IntakePublicSubmit(BaseModel):
    first_name: str
    last_name: str
    birth_date: date
    sex: str
    whatsapp: Optional[str] = None
    email: Optional[EmailStr] = None  # No requerido
    country: str
    city: str
    objective: str
    disliked_foods: Optional[str] = None
```

Campos ELIMINADOS del registro público: `diseases`, `medications`, `food_allergies`, `foods_avoided`, `medical_history`, `dietary_style`, `food_preferences`, `meal_schedule`, `water_intake_liters`, `stress_level`, `sleep_quality`, `sleep_hours`, `budget_level`, `activity_level`, `adherence_level`, `exercise_frequency_per_week`, `exercise_type`, `extra_notes`, `weight_kg`, `height_cm`, `neck_cm`, `chest_cm`, `waist_cm`, `hip_cm`, `leg_cm`, `calf_cm`.

- [ ] **Step 2: Verificar sintaxis**

```bash
cd backend && source .venv/bin/activate && python -c "from app.schemas import IntakePublicSubmit; print('OK')"
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/schemas.py
git commit -m "refactor: simplify IntakePublicSubmit — remove clinical and measurements fields"
```

---

### Task 2: Backend schemas — limpiar IntakeUpdateSubmit

**Files:**
- Modify: `backend/app/schemas.py:300-311`

Quitar `email` y `height_cm` del schema de actualización (el email es para recibir avisos, no se cambia; la altura no varía en adultos).

- [ ] **Step 1: Reemplazar IntakeUpdateSubmit**

```python
class IntakeUpdateSubmit(BaseModel):
    """Campos opcionales para actualización de paciente existente vía link.
    Sin email (es para contacto/avisos, no se cambia aquí).
    Sin altura ni datos clínicos (solo el médico modifica eso)."""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    whatsapp: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None
    weight_kg: Optional[float] = None
```

- [ ] **Step 2: Verificar sintaxis**

```bash
cd backend && source .venv/bin/activate && python -c "from app.schemas import IntakeUpdateSubmit; print('OK')"
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/schemas.py
git commit -m "refactor: remove email and height_cm from IntakeUpdateSubmit"
```

---

### Task 3: Backend endpoint — limpiar public_submit

**Files:**
- Modify: `backend/app/api/intake_links.py:126-248`

El endpoint `public_submit` ya no recibe datos clínicos ni medidas. Solo crea `Patient` + `PatientProfile` parcial (objective, disliked_foods). No crea `PatientMetrics`.

- [ ] **Step 1: Reemplazar el bloque de creación de profile y metrics**

Después de `patient.updated_at = utcnow()` (línea 183), reemplazar el bloque de profile:

```python
    # Profile parcial — solo lo que el paciente puede llenar
    prof_result = await db.execute(
        select(PatientProfile).where(PatientProfile.patient_id == patient.id)
    )
    profile = prof_result.scalar_one_or_none()
    if profile is None:
        profile = PatientProfile(patient_id=patient.id)
        db.add(profile)

    profile.objective = body.objective
    profile.disliked_foods = body.disliked_foods
    profile.completed_by_patient = True
    profile.completed_at = utcnow()
    profile.updated_at = utcnow()

    # NO crear PatientMetrics — el doctor llena medidas en consulta
```

Y eliminar todo el bloque `metric = PatientMetrics(...)` (líneas 217-230).

- [ ] **Step 2: Verificar sintaxis**

```bash
cd backend && source .venv/bin/activate && python -c "from app.api.intake_links import router; print('OK')"
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/api/intake_links.py
git commit -m "refactor: public_submit no longer creates metrics or clinical profile fields"
```

---

### Task 4: Backend endpoint — limpiar public_update

**Files:**
- Modify: `backend/app/api/intake_links.py:281-307`

Quitar `email` de los campos que se actualizan. Quitar `height_cm` de las métricas.

- [ ] **Step 1: Reemplazar el bloque de actualización de patient**

Cambiar:
```python
    patient_fields = [
        "first_name", "last_name", "whatsapp", "email",
        "country", "city",
    ]
```
a:
```python
    patient_fields = [
        "first_name", "last_name", "whatsapp",
        "country", "city",
    ]
```

- [ ] **Step 2: Reemplazar metric_fields para quitar height_cm**

Cambiar:
```python
    metric_fields = ["weight_kg", "height_cm"]
```
a:
```python
    metric_fields = ["weight_kg"]
```

- [ ] **Step 3: Verificar sintaxis**

```bash
cd backend && source .venv/bin/activate && python -c "from app.api.intake_links import router; print('OK')"
```

- [ ] **Step 4: Commit**

```bash
git add backend/app/api/intake_links.py
git commit -m "refactor: remove email and height_cm from public_update"
```

---

### Task 5: Frontend — LocationSelector component

**Files:**
- Create: `frontend/src/components/LocationSelector.tsx`
- Modify: `frontend/package.json` (add dependency)

Componente de país/ciudad con búsqueda vía API, en español.

- [ ] **Step 1: Elegir API de ciudades y agregar dependencia**

Usar `country-state-city` package (no requiere API key, datos empaquetados, nombres en inglés pero podemos mapear):

```bash
cd frontend && npm install country-state-city
```

Este paquete provee `getAllCountries()`, `getStatesOfCountry()`, `getCitiesOfState()`.

Para tener los nombres de países en español, usar REST Countries API para obtener el mapping.

- [ ] **Step 2: Crear LocationSelector.tsx**

```tsx
import { useEffect, useState, useMemo, useCallback } from "react"
import { getAllCountries, getStatesOfCountry, getCitiesOfState } from "country-state-city"
import type { ICountry, IState, ICity } from "country-state-city"

const COUNTRY_NAMES_ES: Record<string, string> = {
  DO: "República Dominicana",
  MX: "México",
  CO: "Colombia",
  CR: "Costa Rica",
  US: "Estados Unidos",
  ES: "España",
  AR: "Argentina",
  CL: "Chile",
  PE: "Perú",
  EC: "Ecuador",
  GT: "Guatemala",
  CU: "Cuba",
  PR: "Puerto Rico",
  VE: "Venezuela",
  PA: "Panamá",
  HN: "Honduras",
  SV: "El Salvador",
  NI: "Nicaragua",
  BO: "Bolivia",
  PY: "Paraguay",
  UY: "Uruguay",
}

interface LocationSelectorProps {
  country: string
  city: string
  onCountryChange: (country: string) => void
  onCityChange: (city: string) => void
  disabled?: boolean
}

export default function LocationSelector({
  country,
  city,
  onCountryChange,
  onCityChange,
  disabled = false,
}: LocationSelectorProps) {
  const allCountries = useMemo(() => getAllCountries(), [])
  const [searchCountry, setSearchCountry] = useState("")
  const [searchCity, setSearchCity] = useState("")

  const selectedCountryCode = useMemo(() => {
    const found = allCountries.find(c => c.name === country || COUNTRY_NAMES_ES[c.isoCode] === country)
    return found?.isoCode || ""
  }, [country, allCountries])

  const filteredCountries = useMemo(() => {
    if (!searchCountry) return allCountries.slice(0, 30)
    const q = searchCountry.toLowerCase()
    return allCountries.filter(c =>
      c.name.toLowerCase().includes(q) ||
      (COUNTRY_NAMES_ES[c.isoCode] || "").toLowerCase().includes(q)
    ).slice(0, 30)
  }, [searchCountry, allCountries])

  const states = useMemo(() => {
    if (!selectedCountryCode) return []
    return getStatesOfCountry(selectedCountryCode) || []
  }, [selectedCountryCode])

  const filteredCities = useMemo(() => {
    if (!selectedCountryCode || states.length === 0) return []
    const foundState = states.find(s => s.name === city)
    if (!foundState) return []
    const cities = getCitiesOfState(selectedCountryCode, foundState.isoCode) || []
    if (!searchCity) return cities.slice(0, 50)
    return cities.filter(c => c.name.toLowerCase().includes(searchCity.toLowerCase())).slice(0, 50)
  }, [selectedCountryCode, states, city, searchCity])

  // Si el país no tiene estados/ciudades, mostrar input libre
  const hasStates = states.length > 0

  const getCountryLabel = useCallback((c: ICountry) => {
    return COUNTRY_NAMES_ES[c.isoCode] || c.name
  }, [])

  return (
    <div className="space-y-4">
      {/* País */}
      <div>
        <label className="block text-sm font-medium text-slate-700 mb-1.5">
          País <span className="text-red-500">*</span>
        </label>
        <div className="relative">
          <input
            type="text"
            placeholder="Buscar país..."
            value={searchCountry}
            onChange={(e) => setSearchCountry(e.target.value)}
            disabled={disabled}
            className="w-full px-3.5 py-2.5 text-sm border border-slate-200 rounded-xl bg-white text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-colors"
          />
          {searchCountry && filteredCountries.length > 0 && (
            <ul className="absolute z-10 mt-1 w-full bg-white border border-slate-200 rounded-xl shadow-lg max-h-48 overflow-y-auto">
              {filteredCountries.map((c) => {
                const label = getCountryLabel(c)
                return (
                  <li
                    key={c.isoCode}
                    onClick={() => { onCountryChange(label); onCityChange(""); setSearchCountry(label); setSearchCity("") }}
                    className={`px-3.5 py-2 text-sm cursor-pointer hover:bg-emerald-50 transition-colors ${label === country ? "bg-emerald-50 text-emerald-700 font-medium" : "text-slate-700"}`}
                  >
                    {label}
                  </li>
                )
              })}
            </ul>
          )}
        </div>
      </div>

      {/* Ciudad */}
      <div>
        <label className="block text-sm font-medium text-slate-700 mb-1.5">
          Ciudad <span className="text-red-500">*</span>
        </label>
        {hasStates ? (
          <div className="relative">
            <input
              type="text"
              placeholder="Buscar ciudad..."
              value={searchCity}
              onChange={(e) => setSearchCity(e.target.value)}
              disabled={disabled || !country}
              className="w-full px-3.5 py-2.5 text-sm border border-slate-200 rounded-xl bg-white text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-colors disabled:opacity-50"
            />
            {searchCity && filteredCities.length > 0 && (
              <ul className="absolute z-10 mt-1 w-full bg-white border border-slate-200 rounded-xl shadow-lg max-h-48 overflow-y-auto">
                {filteredCities.map((c) => (
                  <li
                    key={`${c.name}-${c.latitude}`}
                    onClick={() => { onCityChange(c.name); setSearchCity(c.name) }}
                    className={`px-3.5 py-2 text-sm cursor-pointer hover:bg-emerald-50 transition-colors ${c.name === city ? "bg-emerald-50 text-emerald-700 font-medium" : "text-slate-700"}`}
                  >
                    {c.name}
                  </li>
                ))}
              </ul>
            )}
          </div>
        ) : (
          <input
            name="city_input"
            type="text"
            placeholder={country ? "Escribe tu ciudad" : "Selecciona un país primero"}
            value={city}
            onChange={(e) => onCityChange(e.target.value)}
            disabled={disabled || !country}
            required
            className="w-full px-3.5 py-2.5 text-sm border border-slate-200 rounded-xl bg-white text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-colors disabled:opacity-50"
          />
        )}
      </div>
    </div>
  )
}
```

- [ ] **Step 3: Verificar build**

```bash
cd frontend && npx tsc --noEmit --pretty 2>&1 | head -30
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/LocationSelector.tsx frontend/package.json
git commit -m "feat: add LocationSelector with searchable country/city dropdowns"
```

---

### Task 6: Frontend — simplificar PublicIntake (modo registro)

**Files:**
- Modify: `frontend/src/pages/PublicIntake.tsx`

Modo registro: quitar medidas corporales, salud/objetivo (dejar solo objetivo + disliked_foods), hábitos. Agregar LocationSelector y label de contacto.

- [ ] **Step 1: Importar LocationSelector y limpiar imports**

Cambiar imports:
```tsx
import { FormEvent, useEffect, useMemo, useState } from "react"
import { useParams } from "react-router-dom"
import { submitIntakeForm, updateIntakeForm, validateIntakeToken } from "../services/api"
import type { IntakePublicMeta } from "../types"
import DatePicker from "../components/ui/DatePicker"
import LocationSelector from "../components/LocationSelector"
import { OBJECTIVE_OPTIONS } from "../constants/objectives"
```

Eliminar imports de: `NoAplicaField`, `WeightInput`, `HeightInput`, `COUNTRY_CITIES`.

Eliminar `COUNTRY_CITIES` constant object (líneas 11-17).

Eliminar estados: `diseases`, `medications`, `foodAllergies`, `foodsAvoided`, `medicalHistory` (líneas 28-31).

Eliminar `cityOptions` memo (línea 37).

- [ ] **Step 2: Simplificar el onSubmit para registro**

Reemplazar el bloque de submit (líneas 95-148) con:

```tsx
    // Register flow — solo datos personales + disliked_foods
    const body: Record<string, unknown> = {
      first_name: str("first_name"),
      last_name: str("last_name"),
      birth_date: birthDate,
      sex: str("sex"),
      country,
      city,
      objective: objective,
      disliked_foods: optStr("disliked_foods"),
      whatsapp: optStr("whatsapp"),
      email: optStr("email") || null,
    }
    if (!country || !city) {
      setError("País y ciudad son obligatorios")
      return
    }
    try {
      await submitIntakeForm(token, body)
      setDone(true)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Submit failed")
    }
```

- [ ] **Step 3: Simplificar el return JSX para modo registro**

Reemplazar la sección de "Medidas corporales" (líneas 307-340) — eliminarla completamente del modo registro. En update mode dejar solo `WeightInput`.

Reemplazar la sección "Salud y objetivo" (líneas 342-378) con solo:

```tsx
              {/* Objetivo y preferencias */}
              {linkType === "register" && (
                <section>
                  <h2 className="text-xs font-semibold text-emerald-600 uppercase tracking-wider mb-4">Objetivo y preferencias</h2>
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-slate-700 mb-1.5">
                        Objetivo principal <span className="text-red-500">*</span>
                      </label>
                      <select name="objective" value={objective} onChange={(e) => setObjective(e.target.value)} required
                        className="w-full px-3.5 py-2.5 text-sm border border-slate-200 rounded-xl bg-white text-slate-800 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-colors">
                        {OBJECTIVE_OPTIONS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-slate-700 mb-1.5">Alimentos que NO te gustan o NO consumes</label>
                      <p className="text-xs text-slate-500 mb-2">Ej: hígado, cilantro, mariscos, picante...</p>
                      <textarea name="disliked_foods" rows={2}
                        className="w-full px-3.5 py-2.5 text-sm border border-slate-200 rounded-xl bg-white text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-colors resize-none" />
                    </div>
                  </div>
                </section>
              )}
```

Eliminar la sección "Hábitos" completa (líneas 382-438).

- [ ] **Step 4: Agregar label de contacto informativo**

Después del campo de WhatsApp, agregar:

```tsx
                  <div className="sm:col-span-2">
                    <p className="text-xs text-slate-500 bg-slate-50 rounded-lg px-3 py-2">
                      El correo y WhatsApp nos ayudan a mantenerte al día con recordatorios y actualizaciones de tu plan.
                    </p>
                  </div>
```

- [ ] **Step 5: Reemplazar selects de país/ciudad con LocationSelector**

En JSX, reemplazar los selects de país/ciudad (líneas 274-303) con:

```tsx
                  <div className="sm:col-span-2">
                    <LocationSelector
                      country={country}
                      city={city}
                      onCountryChange={(c) => { setCountry(c); setCity("") }}
                      onCityChange={setCity}
                    />
                  </div>
```

- [ ] **Step 6: Agregar imports y variables faltantes**

Agregar `WeightInput` al import si aún se usa en modo update:

En update mode, reemplazar la sección de medidas (líneas 307-340) con solo peso:

```tsx
              {/* Actualizar peso — solo en modo update */}
              {linkType === "update" && (
                <section>
                  <h2 className="text-xs font-semibold text-emerald-600 uppercase tracking-wider mb-4">Actualizar peso</h2>
                  <div className="max-w-xs">
                    <label className="block text-sm font-medium text-slate-700 mb-1.5">Peso (kg)</label>
                    <input name="weight_kg" type="number" step="0.1" value={weightKg} onChange={(e) => setWeightKg(e.target.value)}
                      className="w-full px-3.5 py-2.5 text-sm border border-slate-200 rounded-xl bg-white text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-colors" />
                  </div>
                </section>
              )}
```

- [ ] **Step 7: Verificar build**

```bash
cd frontend && npx tsc --noEmit --pretty 2>&1 | head -30
```

- [ ] **Step 8: Commit**

```bash
git add frontend/src/pages/PublicIntake.tsx
git commit -m "refactor: simplify PublicIntake register form — only personal data + disliked_foods; update mode: only country/city/weight"
```

---

### Task 7: Frontend — reorganizar Perfil Clínico en PatientDetail

**Files:**
- Modify: `frontend/src/pages/PatientDetail.tsx`

El Perfil Clínico ya existe en el admin panel pero está todo en una sola sección. Reorganizar en 4 sub-secciones: Medidas, Historial Clínico, Perfil Nutricional, Estilo de Vida.

- [ ] **Step 1: Navegar al Perfil Clínico existente**

Ubicar la sección de Perfil Clínico (alrededor de línea 400-600, buscar "Perfil Clínico" o "Perfil Clinico"). La sección actual tiene todos los campos en un solo `<div>` con `className="grid grid-cols-1 sm:grid-cols-2 gap-4"`.

- [ ] **Step 2: Agregar indicador de "Pendiente de evaluación"**

Agregar un badge condicional al inicio de la sección de Perfil Clínico que indique si el perfil está completo o pendiente:

```tsx
{!profileCompleted && (
  <div className="mb-4 rounded-xl bg-amber-50 border border-amber-200 px-4 py-3 flex items-center gap-2">
    <span className="text-amber-600 text-sm">⚠️</span>
    <p className="text-sm text-amber-700">Pendiente de evaluación clínica — completa los datos del paciente en consulta</p>
  </div>
)}
```

`profileCompleted` se determina si `food_allergies` tiene valor (es el campo clínico más importante).

- [ ] **Step 3: Reorganizar en 4 sub-secciones con divisores visuales**

Ejemplo de estructura (dentro del bloque de edición del perfil clínico):

```tsx
<h3 className="text-lg font-semibold text-slate-800 mb-4">Perfil Clínico</h3>

{/* Medidas Corporales */}
<div className="mb-6 p-4 bg-slate-50 rounded-xl">
  <h4 className="text-sm font-semibold text-emerald-600 uppercase tracking-wider mb-3">Medidas Corporales</h4>
  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
    {/* weight_kg, height_cm, neck_cm, chest_cm, waist_cm, hip_cm, leg_cm, calf_cm */}
  </div>
</div>

{/* Historial Clínico */}
<div className="mb-6 p-4 bg-slate-50 rounded-xl">
  <h4 className="text-sm font-semibold text-emerald-600 uppercase tracking-wider mb-3">Historial Clínico</h4>
  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
    {/* diseases, medications, medical_history, food_allergies */}
  </div>
</div>

{/* Perfil Nutricional */}
<div className="mb-6 p-4 bg-slate-50 rounded-xl">
  <h4 className="text-sm font-semibold text-emerald-600 uppercase tracking-wider mb-3">Perfil Nutricional</h4>
  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
    {/* dietary_style, food_preferences, foods_avoided, water_intake, meal_schedule */}
  </div>
</div>

{/* Estilo de Vida */}
<div className="mb-6 p-4 bg-slate-50 rounded-xl">
  <h4 className="text-sm font-semibold text-emerald-600 uppercase tracking-wider mb-3">Estilo de Vida</h4>
  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
    {/* todos los campos de estilo de vida */}
  </div>
</div>
```

Nota: Los campos INPUT/EDIT ya existen con sus handlers y estado. Solo se está reordenando visualmente la sección en 4 grupos con fondos y títulos. NO cambiar la lógica de los handlers ni del submit.

- [ ] **Step 4: Verificar build**

```bash
cd frontend && npx tsc --noEmit --pretty 2>&1 | head -30
```

- [ ] **Step 5: Commit**

```bash
git add frontend/src/pages/PatientDetail.tsx
git commit -m "feat: reorganize Perfil Clinico into 4 sub-sections with pending evaluation indicator"
```

---

### Task 8: Verificación general

**Files:**
- All modified files

- [ ] **Step 1: Backend carga correctamente**

```bash
cd backend && source .venv/bin/activate && python -c "from app.main import app; print('Backend OK:', len(app.routes))"
```

- [ ] **Step 2: Frontend build**

```bash
cd frontend && npx tsc --noEmit && npm run build 2>&1 | tail -10
```

---

## Resumen de cambios

| Archivo | Cambio |
|---------|--------|
| `backend/app/schemas.py:261-298` | IntakePublicSubmit simplificado a 10 campos |
| `backend/app/schemas.py:300-311` | IntakeUpdateSubmit sin email ni height_cm |
| `backend/app/api/intake_links.py:185-230` | public_submit ya no crea PatientMetrics ni perfil clínico |
| `backend/app/api/intake_links.py:281-307` | public_update sin email ni height_cm |
| `frontend/src/components/LocationSelector.tsx` | **Nuevo** — selector país/ciudad con búsqueda |
| `frontend/package.json` | + `country-state-city` dependency |
| `frontend/src/pages/PublicIntake.tsx` | Modo registro: solo 10 campos + LocationSelector + label contacto |
| `frontend/src/pages/PublicIntake.tsx` | Modo update: LocationSelector + solo peso (sin email, sin altura) |
| `frontend/src/pages/PatientDetail.tsx` | Perfil Clínico reorganizado en 4 sub-secciones + badge pendiente |
