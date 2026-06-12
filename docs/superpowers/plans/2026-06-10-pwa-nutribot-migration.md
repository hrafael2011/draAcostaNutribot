# PWA Nutribot + Links Compartibles — Plan de Implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Migrar generación de dietas de Telegram a PWA web/mobile con wizard multi-paso, links compartibles (WhatsApp/Email/Copiar) para registro y actualización de pacientes, diseño Natural/Salud (emerald-600), logo de la doctora integrado profesionalmente en login y panel.

**Architecture:** FastAPI backend existente (sin cambios estructurales) + 5 nuevos endpoints REST. Frontend React 19 existente mejorado con Tailwind CSS responsive, TanStack Query, wizard de 7 pasos, PWA con service worker. Corte directo de Telegram al final.

**Tech Stack:** FastAPI, SQLAlchemy async, PostgreSQL, React 19, TypeScript 5.7, Vite 7, Tailwind CSS 4, TanStack Query 5, vite-plugin-pwa

**Design System:** Natural/Salud — emerald-600 (#059669), fondo blanco, bordes rounded-xl, sombras shadow-sm/md, tipografía system sans-serif

---

## Fase 0: Setup y Assets (Día 1)

### Task 0.1: Procesar logo para todos los formatos

- [ ] **Step 1: Convertir logo JPEG a formatos necesarios**

```bash
cd "/home/hendrick-rafael/Desktop/Proyectos Oficiales/diet_telegram_agent"
mkdir -p frontend/public

python3 -c "
from PIL import Image

img = Image.open('logo-doctora.jpeg').convert('RGBA')

# Login page: 240px wide (mantiene proporción)
h = int(240 * img.height / img.width)
img.resize((240, h), Image.LANCZOS).save('frontend/public/logo-login.webp', 'WEBP', quality=85)

# Sidebar: 96px wide
h = int(96 * img.height / img.width)
img.resize((96, h), Image.LANCZOS).save('frontend/public/logo-sidebar.webp', 'WEBP', quality=85)

# Mobile top bar: 48px wide
h = int(48 * img.height / img.width)
img.resize((48, h), Image.LANCZOS).save('frontend/public/logo-mobile.webp', 'WEBP', quality=85)

# Favicon 32x32 PNG
img_32 = img.resize((32, 32), Image.LANCZOS)
img_32.save('frontend/public/favicon-32.png', 'PNG')

# PWA icons
img_192 = img.resize((192, 192), Image.LANCZOS)
img_192.save('frontend/public/icon-192.png', 'PNG')
img_512 = img.resize((512, 512), Image.LANCZOS)
img_512.save('frontend/public/icon-512.png', 'PNG')

# Apple touch icon
img_180 = img.resize((180, 180), Image.LANCZOS)
img_180.save('frontend/public/apple-icon-180.png', 'PNG')

print('All logo formats generated')
"
```

- [ ] **Step 2: Agregar favicon al index.html**

Read `frontend/index.html`, add inside `<head>`:
```html
<link rel="icon" type="image/png" sizes="32x32" href="/favicon-32.png" />
<link rel="apple-touch-icon" sizes="180x180" href="/apple-icon-180.png" />
```

- [ ] **Step 3: Commit**

```bash
git add frontend/public/logo-*.webp frontend/public/icon-*.png frontend/public/favicon-*.png frontend/public/apple-icon-*.png frontend/index.html
git commit -m "feat: add logo assets in all formats (webp + png) and favicon"
```

### Task 0.2: Instalar dependencias frontend

- [ ] **Step 1: Instalar paquetes**

```bash
cd "/home/hendrick-rafael/Desktop/Proyectos Oficiales/diet_telegram_agent/frontend"
npm install @tanstack/react-query tailwindcss @tailwindcss/vite vite-plugin-pwa
```

- [ ] **Step 2: Configurar Tailwind en vite.config.ts**

Read `frontend/vite.config.ts`, replace with:
```typescript
import { defineConfig } from "vite"
import react from "@vitejs/plugin-react"
import tailwindcss from "@tailwindcss/vite"
import { VitePWA } from "vite-plugin-pwa"

export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
    VitePWA({
      registerType: "autoUpdate",
      manifest: {
        name: "Dra. Acosta Nutribot",
        short_name: "Nutribot",
        description: "Plataforma profesional de gestión nutricional",
        theme_color: "#059669",
        background_color: "#ffffff",
        display: "standalone",
        orientation: "portrait",
        icons: [
          { src: "/icon-192.png", sizes: "192x192", type: "image/png" },
          { src: "/icon-512.png", sizes: "512x512", type: "image/png" },
        ],
      },
      workbox: {
        globPatterns: ["**/*.{js,css,html,ico,png,svg,webp}"],
        runtimeCaching: [
          {
            urlPattern: /^https?:\/\/.*\/api\/diets\/\d+$/,
            handler: "NetworkFirst",
            options: {
              cacheName: "diet-detail",
              expiration: { maxEntries: 50 },
            },
          },
        ],
      },
    }),
  ],
  server: {
    port: 5173,
  },
})
```

- [ ] **Step 3: Importar Tailwind en main.tsx**

Read `frontend/src/main.tsx`, add at top:
```typescript
import "tailwindcss"
```

- [ ] **Step 4: Verificar build**

```bash
cd "/home/hendrick-rafael/Desktop/Proyectos Oficiales/diet_telegram_agent/frontend"
npm run build
```
Expected: Build succeeds, `dist/` contains service worker files

- [ ] **Step 5: Commit**

```bash
git add frontend/package.json frontend/package-lock.json frontend/vite.config.ts frontend/src/main.tsx
git commit -m "feat: add Tailwind CSS, TanStack Query, and PWA plugin"
```

---

## Fase 1: Backend — Nuevos Endpoints (Día 2-3)

### Task 1.1: Schemas para aprobar/descartar/ajustar/editar

**Files:**
- Modify: `backend/app/schemas.py`

- [ ] **Step 1: Agregar nuevos schemas al final de schemas.py**

```python
# --- Diet approval / discard / quick-adjust / meal edit ---

class DietQuickAdjustRequest(BaseModel):
    adjustment: str = Field(..., min_length=1, max_length=200)


class DietMealUpdate(BaseModel):
    day_index: int = Field(..., ge=0, le=55)
    slot_key: str = Field(..., min_length=1, max_length=40)
    meal_text: str = Field(..., min_length=1, max_length=3500)


class DietMealsUpdateRequest(BaseModel):
    meals: list[DietMealUpdate] = Field(..., min_length=1, max_length=56)
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/schemas.py
git commit -m "feat: add DietQuickAdjustRequest, DietMealUpdate, DietMealsUpdateRequest schemas"
```

### Task 1.2: Servicio update_diet_meals

**Files:**
- Modify: `backend/app/services/diet_service.py`

- [ ] **Step 1: Agregar update_diet_meals() en diet_service.py**

Después de `discard_diet_preview()` (línea 343), agregar:
```python
async def update_diet_meals(
    db: AsyncSession,
    doctor: Doctor,
    diet_id: int,
    meals: list[dict[str, Any]],
) -> Diet:
    diet = await _diet_for_update(db, diet_id, doctor.id)
    if diet is None:
        raise DietGenerationError("not_found", "Diet not found")
    if diet.status != "pending_approval":
        raise DietGenerationError(
            "invalid_state",
            "Solo se pueden editar comidas de borradores pendientes de aprobación",
        )

    plan = dict(diet.structured_plan_json) if isinstance(diet.structured_plan_json, dict) else {}
    days = plan.get("days")
    if not isinstance(days, list):
        raise DietGenerationError("invalid_plan", "El plan no tiene estructura de días")

    for meal_update in meals:
        day_index = meal_update["day_index"]
        slot_key = meal_update["slot_key"]
        meal_text = meal_update["meal_text"]

        if day_index < 0 or day_index >= len(days):
            continue
        day = days[day_index]
        if not isinstance(day, dict):
            continue
        meals_dict = day.get("meals") if isinstance(day.get("meals"), dict) else {}
        old_text = meals_dict.get(slot_key, "") if isinstance(meals_dict, dict) else ""
        meals_dict[slot_key] = meal_text
        day["meals"] = meals_dict
        day[slot_key] = meal_text

        db.add(
            AuditLog(
                doctor_id=doctor.id,
                action="diet_edit_meal_web",
                entity_type="diet",
                entity_id=diet.id,
                payload_json={
                    "patient_id": diet.patient_id,
                    "day": day_index + 1,
                    "slot": slot_key,
                    "old_text_length": len(str(old_text)),
                    "new_text_length": len(meal_text),
                    "channel": "web",
                },
            )
        )

    diet.structured_plan_json = plan
    diet.updated_at = utcnow()
    return diet
```

Verificar imports al inicio del archivo: agregar `Any` al typing import si no existe.

- [ ] **Step 2: Commit**

```bash
git add backend/app/services/diet_service.py
git commit -m "feat: add update_diet_meals() service for web meal editing"
```

### Task 1.3: Endpoints approve, discard, quick-adjust, meals

**Files:**
- Modify: `backend/app/api/diets.py`

- [ ] **Step 1: Agregar nuevos endpoints en diets.py**

Después del endpoint `regenerate_diet_route` (línea 180), agregar:

```python
from app.schemas import (
    DietGenerateRequest,
    DietMealsUpdateRequest,
    DietOut,
    DietQuickAdjustRequest,
    DietRegenerateRequest,
    DietVersionSummary,
    PaginatedDiets,
    PlanDurationPresetsOut,
)
from app.services.diet_service import (
    DietGenerationError,
    approve_diet_preview,
    create_new_diet,
    discard_diet_preview,
    regenerate_diet,
    update_diet_meals,
)


@router.post("/{diet_id}/approve", response_model=DietOut)
async def approve_diet(
    diet_id: int,
    db: AsyncSession = Depends(get_db),
    doctor: Doctor = Depends(get_current_doctor),
):
    try:
        diet = await approve_diet_preview(db, doctor, diet_id)
        await db.commit()
        await db.refresh(diet)
        return diet
    except DietGenerationError as e:
        await db.rollback()
        raise _http_from_diet_error(e) from e


@router.post("/{diet_id}/discard", response_model=DietOut)
async def discard_diet(
    diet_id: int,
    db: AsyncSession = Depends(get_db),
    doctor: Doctor = Depends(get_current_doctor),
):
    try:
        diet = await discard_diet_preview(db, doctor, diet_id)
        await db.commit()
        await db.refresh(diet)
        return diet
    except DietGenerationError as e:
        await db.rollback()
        raise _http_from_diet_error(e) from e


@router.post("/{diet_id}/quick-adjust", response_model=DietOut)
async def quick_adjust_diet(
    diet_id: int,
    body: DietQuickAdjustRequest,
    db: AsyncSession = Depends(get_db),
    doctor: Doctor = Depends(get_current_doctor),
):
    try:
        diet = await regenerate_diet(
            db,
            doctor,
            diet_id,
            body.adjustment,
            diet_status="pending_approval",
        )
        await db.commit()
        await db.refresh(diet)
        return diet
    except DietGenerationError as e:
        await db.rollback()
        raise _http_from_diet_error(e) from e


@router.patch("/{diet_id}/meals", response_model=DietOut)
async def edit_diet_meals(
    diet_id: int,
    body: DietMealsUpdateRequest,
    db: AsyncSession = Depends(get_db),
    doctor: Doctor = Depends(get_current_doctor),
):
    try:
        meals_dicts = [
            {"day_index": m.day_index, "slot_key": m.slot_key, "meal_text": m.meal_text}
            for m in body.meals
        ]
        diet = await update_diet_meals(db, doctor, diet_id, meals_dicts)
        await db.commit()
        await db.refresh(diet)
        return diet
    except DietGenerationError as e:
        await db.rollback()
        raise _http_from_diet_error(e) from e
```

- [ ] **Step 2: Verificar que el router existente compile**

```bash
cd "/home/hendrick-rafael/Desktop/Proyectos Oficiales/diet_telegram_agent/backend"
python -c "from app.api.diets import router; print('OK')"
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/api/diets.py
git commit -m "feat: add approve, discard, quick-adjust, and edit-meals endpoints"
```

### Task 1.4: Modificar endpoint generate para aceptar pending_approval

**Files:**
- Modify: `backend/app/api/diets.py`
- Modify: `backend/app/schemas.py`

- [ ] **Step 1: Agregar query param al endpoint generate_diet**

En la función `generate_diet`, agregar parámetro:
```python
@router.post("/generate", response_model=DietOut, status_code=status.HTTP_201_CREATED)
async def generate_diet(
    body: DietGenerateRequest,
    db: AsyncSession = Depends(get_db),
    doctor: Doctor = Depends(get_current_doctor),
    pending: bool = Query(False, description="Create as pending_approval instead of generated"),
):
    try:
        diet_status = "pending_approval" if pending else "generated"
        diet = await create_new_diet(
            db,
            doctor,
            body.patient_id,
            body.doctor_instruction,
            diet_status=diet_status,
            # ... rest of params unchanged
        )
```

- [ ] **Step 2: Agregar import de Query**

Verificar que `Query` está en los imports de fastapi.

- [ ] **Step 3: Commit**

```bash
git add backend/app/api/diets.py
git commit -m "feat: add ?pending=true query param to generate endpoint"
```

### Task 1.5: Modificar intake submit para actualización de pacientes existentes

**Files:**
- Modify: `backend/app/api/intake_links.py`
- Modify: `backend/app/schemas.py`

- [ ] **Step 1: Agregar IntakeUpdateSubmit schema**

```python
class IntakeUpdateSubmit(BaseModel):
    """Campos opcionales para actualización de paciente existente."""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    birth_date: Optional[date] = None
    sex: Optional[str] = None
    whatsapp: Optional[str] = None
    email: Optional[EmailStr] = None
    country: Optional[str] = None
    city: Optional[str] = None
    objective: Optional[str] = None
    diseases: Optional[str] = None
    medications: Optional[str] = None
    food_allergies: Optional[str] = None
    foods_avoided: Optional[str] = None
    dietary_style: Optional[str] = None
    food_preferences: Optional[str] = None
    disliked_foods: Optional[str] = None
    water_intake_liters: Optional[float] = None
    activity_level: Optional[str] = None
    stress_level: Optional[int] = None
    sleep_quality: Optional[int] = None
    sleep_hours: Optional[float] = None
    budget_level: Optional[str] = None
    adherence_level: Optional[int] = None
    exercise_frequency_per_week: Optional[int] = None
    exercise_type: Optional[str] = None
    extra_notes: Optional[str] = None
    weight_kg: Optional[float] = None
    height_cm: Optional[float] = None
    neck_cm: Optional[float] = None
    chest_cm: Optional[float] = None
    waist_cm: Optional[float] = None
    hip_cm: Optional[float] = None
    leg_cm: Optional[float] = None
    calf_cm: Optional[float] = None
```

- [ ] **Step 2: Agregar endpoint PUT /public/{token}/update en intake_links.py**

```python
@router.put("/public/{token}/update", status_code=status.HTTP_200_OK)
async def public_update(
    token: str,
    body: IntakeUpdateSubmit,
    db: AsyncSession = Depends(get_db),
):
    """Actualizar datos de un paciente existente mediante link."""
    result = await db.execute(
        select(PatientIntakeLink).where(PatientIntakeLink.token == token)
    )
    link = result.scalar_one_or_none()
    if link is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid link")
    now = utcnow()
    if link.status == "revoked":
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="Link revoked")
    if link.expires_at < now:
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="Link expired")
    if link.use_count >= link.max_uses:
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="Link already used")
    if link.patient_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This link is for new patient registration, use POST /submit",
        )

    patient = await db.get(Patient, link.patient_id)
    if patient is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")

    # Actualizar solo campos provistos
    patient_fields = {
        "first_name", "last_name", "birth_date", "sex", "whatsapp", "email",
        "country", "city",
    }
    for field in patient_fields:
        value = getattr(body, field, None)
        if value is not None:
            setattr(patient, field, value)
    patient.updated_at = utcnow()

    # Actualizar perfil
    profile_fields = {
        "objective", "diseases", "medications", "food_allergies", "foods_avoided",
        "dietary_style", "food_preferences", "disliked_foods", "water_intake_liters",
        "activity_level", "stress_level", "sleep_quality", "sleep_hours",
        "budget_level", "adherence_level", "exercise_frequency_per_week",
        "exercise_type", "extra_notes",
    }
    has_profile_update = any(getattr(body, f, None) is not None for f in profile_fields)
    if has_profile_update:
        pr = await db.execute(
            select(PatientProfile).where(PatientProfile.patient_id == patient.id)
        )
        profile = pr.scalar_one_or_none()
        if profile is None:
            profile = PatientProfile(patient_id=patient.id)
            db.add(profile)
        for field in profile_fields:
            value = getattr(body, field, None)
            if value is not None:
                setattr(profile, field, value)
        profile.updated_at = utcnow()

    # Agregar métrica si hay medidas
    metric_fields = {
        "weight_kg", "height_cm", "neck_cm", "chest_cm", "waist_cm",
        "hip_cm", "leg_cm", "calf_cm",
    }
    has_metric = any(getattr(body, f, None) is not None for f in metric_fields)
    if has_metric:
        metric = PatientMetrics(
            patient_id=patient.id,
            recorded_at=utcnow(),
            source="intake_update",
        )
        for field in metric_fields:
            value = getattr(body, field, None)
            if value is not None:
                setattr(metric, field, value)
        db.add(metric)

    link.use_count += 1
    link.last_used_at = utcnow()
    link.updated_at = utcnow()
    if link.use_count >= link.max_uses:
        link.status = "completed"

    db.add(
        AuditLog(
            doctor_id=link.doctor_id,
            action="intake_update",
            entity_type="patient",
            entity_id=patient.id,
            payload_json={"intake_link_id": link.id},
        )
    )
    await db.commit()
    return {"ok": True}
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/schemas.py backend/app/api/intake_links.py
git commit -m "feat: add IntakeUpdateSubmit schema and PUT /public/{token}/update endpoint"
```

---

## Fase 2: Componentes UI Base + Logo (Día 4-5)

### Task 2.1: Componentes UI genéricos (Button, Card, Stepper, Accordion)

**Files:**
- Create: `frontend/src/components/ui/Button.tsx`
- Create: `frontend/src/components/ui/Card.tsx`
- Create: `frontend/src/components/ui/Stepper.tsx`
- Create: `frontend/src/components/ui/Accordion.tsx`

- [ ] **Step 1: Button.tsx**

```typescript
import type { ButtonHTMLAttributes, ReactNode } from "react"

type ButtonVariant = "primary" | "secondary" | "danger" | "ghost"

const variantStyles: Record<ButtonVariant, string> = {
  primary:
    "bg-emerald-600 text-white hover:bg-emerald-700 focus:ring-emerald-500 shadow-sm",
  secondary:
    "bg-white text-gray-700 border border-gray-300 hover:bg-gray-50 focus:ring-emerald-500",
  danger:
    "bg-red-500 text-white hover:bg-red-600 focus:ring-red-500",
  ghost:
    "bg-transparent text-gray-600 hover:bg-gray-100 focus:ring-gray-400",
}

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: ButtonVariant
  children: ReactNode
}

export default function Button({
  variant = "primary",
  children,
  className = "",
  ...props
}: ButtonProps) {
  return (
    <button
      className={`inline-flex items-center justify-center rounded-lg px-4 py-2 text-sm font-medium
        transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2
        disabled:opacity-50 disabled:cursor-not-allowed
        ${variantStyles[variant]} ${className}`}
      {...props}
    >
      {children}
    </button>
  )
}
```

- [ ] **Step 2: Card.tsx**

```typescript
import type { ReactNode, HTMLAttributes } from "react"

type CardProps = HTMLAttributes<HTMLDivElement> & {
  children: ReactNode
  selected?: boolean
}

export default function Card({
  children,
  selected = false,
  className = "",
  ...props
}: CardProps) {
  return (
    <div
      className={`rounded-xl border bg-white p-4 transition-shadow
        ${selected ? "border-emerald-500 bg-emerald-50 shadow-md ring-1 ring-emerald-500" : "border-gray-200 shadow-sm hover:shadow-md"}
        ${className}`}
      {...props}
    >
      {children}
    </div>
  )
}
```

- [ ] **Step 3: Stepper.tsx**

```typescript
type StepperProps = {
  steps: { label: string }[]
  current: number
}

export default function Stepper({ steps, current }: StepperProps) {
  return (
    <nav aria-label="Progress" className="w-full">
      {/* Mobile: dots */}
      <ol className="flex items-center justify-center gap-1 md:hidden">
        {steps.map((s, i) => (
          <li key={i}>
            <span
              className={`flex h-6 w-6 items-center justify-center rounded-full text-xs font-medium
                ${i <= current ? "bg-emerald-600 text-white" : "bg-gray-200 text-gray-500"}`}
              aria-current={i === current ? "step" : undefined}
            >
              {i + 1}
            </span>
          </li>
        ))}
      </ol>
      {/* Desktop: labels */}
      <ol className="hidden md:flex items-center gap-2">
        {steps.map((s, i) => (
          <li key={i} className="flex items-center gap-2">
            <span
              className={`flex h-7 w-7 items-center justify-center rounded-full text-xs font-bold
                ${i < current ? "bg-emerald-600 text-white" : i === current ? "bg-emerald-600 text-white ring-4 ring-emerald-100" : "bg-gray-200 text-gray-500"}`}
            >
              {i < current ? "✓" : i + 1}
            </span>
            <span
              className={`text-sm ${i <= current ? "font-semibold text-emerald-700" : "text-gray-400"}`}
            >
              {s.label}
            </span>
            {i < steps.length - 1 && (
              <span className="mx-1 h-px w-8 bg-gray-300 hidden lg:block" />
            )}
          </li>
        ))}
      </ol>
    </nav>
  )
}
```

- [ ] **Step 4: Accordion.tsx**

```typescript
import { useState, type ReactNode } from "react"

type AccordionProps = {
  title: string
  children: ReactNode
  defaultOpen?: boolean
}

export default function Accordion({
  title,
  children,
  defaultOpen = false,
}: AccordionProps) {
  const [open, setOpen] = useState(defaultOpen)
  return (
    <div className="rounded-lg border border-gray-200">
      <button
        type="button"
        className="flex w-full items-center justify-between rounded-lg px-4 py-3 text-left text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
        onClick={() => setOpen(!open)}
        aria-expanded={open}
      >
        {title}
        <svg
          className={`h-4 w-4 transform transition-transform ${open ? "rotate-180" : ""}`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>
      {open && <div className="border-t border-gray-200 px-4 py-3">{children}</div>}
    </div>
  )
}
```

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/ui/
git commit -m "feat: add reusable UI components (Button, Card, Stepper, Accordion)"
```

### Task 2.2: Integrar logo en Login

**Files:**
- Modify: `frontend/src/pages/Login.tsx`

- [ ] **Step 1: Leer Login.tsx actual y agregar logo + diseño Tailwind**

Reemplazar la página de login con:

```typescript
import { useState, type FormEvent } from "react"
import { useNavigate, useLocation } from "react-router-dom"
import { useAuth } from "../context/AuthContext"
import Button from "../components/ui/Button"

export default function Login() {
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [error, setError] = useState("")
  const [loading, setLoading] = useState(false)
  const { login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  const from = (location.state as { from?: string })?.from || "/dashboard"

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError("")
    setLoading(true)
    try {
      await login(email, password)
      navigate(from, { replace: true })
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al iniciar sesión")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 px-4">
      <div className="w-full max-w-sm">
        {/* Logo + nombre */}
        <div className="mb-8 text-center">
          <img
            src="/logo-login.webp"
            alt="Dra. Acosta Nutribot"
            className="mx-auto mb-4 rounded-2xl shadow-md"
            width={180}
            height={174}
          />
          <h1 className="text-xl font-bold text-gray-800">Dra. Acosta</h1>
          <p className="text-sm text-gray-500">Nutribot — Gestión Nutricional</p>
        </div>

        {/* Formulario */}
        <form
          onSubmit={handleSubmit}
          className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm"
        >
          {error && (
            <div className="mb-4 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">
              {error}
            </div>
          )}

          <label className="mb-1 block text-sm font-medium text-gray-700">
            Correo electrónico
          </label>
          <input
            type="email"
            required
            autoFocus
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="doctora@ejemplo.com"
            className="mb-4 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm
              focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
          />

          <label className="mb-1 block text-sm font-medium text-gray-700">
            Contraseña
          </label>
          <input
            type="password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="mb-6 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm
              focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
          />

          <Button type="submit" disabled={loading} className="w-full">
            {loading ? "Iniciando sesión..." : "Iniciar sesión"}
          </Button>
        </form>
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/pages/Login.tsx
git commit -m "feat: redesign login page with logo and Tailwind styling"
```

### Task 2.3: Integrar logo en AdminLayout (sidebar + top bar mobile)

**Files:**
- Modify: `frontend/src/layouts/AdminLayout.tsx`

- [ ] **Step 1: Leer y refactorizar AdminLayout con Tailwind + logo + responsive**

```typescript
import { useState } from "react"
import { Outlet, NavLink, useNavigate } from "react-router-dom"
import { useAuth } from "../context/AuthContext"
import { getDoctorMe } from "../services/api"
import { useEffect } from "react"

type DoctorMe = { full_name: string; email: string; role: string }

export default function AdminLayout() {
  const [doctor, setDoctor] = useState<DoctorMe | null>(null)
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const { logout } = useAuth()
  const navigate = useNavigate()

  useEffect(() => {
    getDoctorMe()
      .then((d) => setDoctor({ full_name: d.full_name, email: d.email, role: d.role }))
      .catch(() => {
        logout()
        navigate("/login")
      })
  }, [])

  const linkClass = ({ isActive }: { isActive: boolean }) =>
    `flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
      isActive
        ? "bg-emerald-100 text-emerald-700"
        : "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
    }`

  const navItems = [
    { to: "/dashboard", label: "Dashboard", icon: "📊" },
    { to: "/patients", label: "Pacientes", icon: "👥" },
    { to: "/diets", label: "Dietas", icon: "🍽️" },
    { to: "/intake-links", label: "Links", icon: "🔗" },
    { to: "/telegram", label: "Telegram", icon: "📱" },
  ]

  if (doctor?.role === "admin") {
    navItems.push({ to: "/admin/users", label: "Usuarios", icon: "⚙️" })
  }

  const SidebarContent = () => (
    <div className="flex h-full flex-col">
      {/* Logo + Doctor info */}
      <div className="flex items-center gap-3 border-b border-gray-200 px-4 py-4">
        <img
          src="/logo-sidebar.webp"
          alt="Logo"
          width={48}
          height={46}
          className="rounded-lg shadow-sm"
        />
        <div className="min-w-0">
          <p className="truncate text-sm font-semibold text-gray-800">
            {doctor?.full_name || "Doctora"}
          </p>
          <p className="truncate text-xs text-gray-500">{doctor?.email}</p>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-1 px-2 py-4">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === "/dashboard"}
            className={linkClass}
            onClick={() => setSidebarOpen(false)}
          >
            <span>{item.icon}</span>
            {item.label}
          </NavLink>
        ))}
      </nav>

      {/* Logout */}
      <div className="border-t border-gray-200 px-2 py-3">
        <button
          type="button"
          onClick={() => logout()}
          className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium text-gray-500 hover:bg-red-50 hover:text-red-600 transition-colors"
        >
          🚪 Cerrar sesión
        </button>
      </div>
    </div>
  )

  return (
    <div className="flex min-h-screen bg-gray-50">
      {/* Desktop sidebar */}
      <aside className="hidden md:flex md:w-60 md:flex-col md:bg-white md:border-r md:border-gray-200 md:fixed md:inset-y-0">
        <SidebarContent />
      </aside>

      {/* Mobile sidebar overlay */}
      {sidebarOpen && (
        <div className="fixed inset-0 z-40 md:hidden">
          <div
            className="fixed inset-0 bg-black/50"
            onClick={() => setSidebarOpen(false)}
          />
          <aside className="fixed inset-y-0 left-0 w-72 bg-white shadow-xl z-50">
            <SidebarContent />
          </aside>
        </div>
      )}

      {/* Main content */}
      <div className="flex flex-1 flex-col md:ml-60">
        {/* Top bar (mobile) */}
        <header className="sticky top-0 z-30 flex items-center gap-3 border-b border-gray-200 bg-white px-4 py-2 md:hidden">
          <button
            type="button"
            onClick={() => setSidebarOpen(true)}
            className="rounded-lg p-1 text-gray-500 hover:bg-gray-100"
            aria-label="Abrir menú"
          >
            <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>
          <img
            src="/logo-mobile.webp"
            alt="Logo"
            width={32}
            height={31}
            className="rounded-md"
          />
          <p className="text-sm font-semibold text-gray-800 truncate">
            {doctor?.full_name || "Nutribot"}
          </p>
        </header>

        {/* Page content */}
        <main className="flex-1 p-4 md:p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/layouts/AdminLayout.tsx
git commit -m "feat: redesign AdminLayout with logo, Tailwind, and responsive sidebar"
```

---

## Fase 3: Wizard de Dieta (Día 6-10)

### Task 3.1: Tipos del wizard

**Files:**
- Modify: `frontend/src/types/index.ts`

- [ ] **Step 1: Agregar tipos del wizard**

```typescript
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
  | { type: "RESET" }

export function wizardReducer(state: WizardState, action: WizardAction): WizardState {
  if (action.type === "SET_FIELD") {
    return { ...state, [action.field]: action.value }
  }
  if (action.type === "SET_DIET") {
    return { ...state, generatedDiet: action.diet }
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
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/types/index.ts
git commit -m "feat: add WizardState, WizardAction, and wizardReducer types"
```

### Task 3.2: Hooks del wizard

**Files:**
- Create: `frontend/src/hooks/useDietGeneration.ts`
- Create: `frontend/src/hooks/usePatientSearch.ts`

- [ ] **Step 1: useDietGeneration.ts**

```typescript
import { useMutation } from "@tanstack/react-query"
import {
  generateDiet,
  regenerateDiet,
  approveDiet,
  discardDiet,
  quickAdjustDiet,
  updateDietMeals,
} from "../services/api"

export function useDietGeneration() {
  const generate = useMutation({
    mutationFn: (body: Parameters<typeof generateDiet>[0]) => generateDiet({ ...body }),
  })

  const regenerate = useMutation({
    mutationFn: ({ id, body }: { id: number; body: Parameters<typeof regenerateDiet>[1] }) =>
      regenerateDiet(id, body),
  })

  const approve = useMutation({
    mutationFn: (dietId: number) => approveDiet(dietId),
  })

  const discard = useMutation({
    mutationFn: (dietId: number) => discardDiet(dietId),
  })

  const quickAdjust = useMutation({
    mutationFn: ({ dietId, adjustment }: { dietId: number; adjustment: string }) =>
      quickAdjustDiet(dietId, adjustment),
  })

  const editMeals = useMutation({
    mutationFn: ({
      dietId,
      meals,
    }: {
      dietId: number
      meals: { day_index: number; slot_key: string; meal_text: string }[]
    }) => updateDietMeals(dietId, { meals }),
  })

  return { generate, regenerate, approve, discard, quickAdjust, editMeals }
}
```

- [ ] **Step 2: usePatientSearch.ts**

```typescript
import { useState, useEffect, useCallback } from "react"
import { getPatients } from "../services/api"
import type { Patient } from "../types"

export function usePatientSearch() {
  const [query, setQuery] = useState("")
  const [results, setResults] = useState<Patient[]>([])
  const [loading, setLoading] = useState(false)

  const search = useCallback(async (q: string) => {
    if (q.trim().length < 2) {
      setResults([])
      return
    }
    setLoading(true)
    try {
      const data = await getPatients({ search: q.trim(), page: 1, page_size: 10 })
      setResults(data.items)
    } catch {
      setResults([])
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    const timer = setTimeout(() => search(query), 300)
    return () => clearTimeout(timer)
  }, [query, search])

  return { query, setQuery, results, loading }
}
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/hooks/
git commit -m "feat: add useDietGeneration and usePatientSearch hooks"
```

### Task 3.3: Funciones API nuevas en el frontend

**Files:**
- Modify: `frontend/src/services/api.ts`

- [ ] **Step 1: Agregar al final de api.ts**

```typescript
export function approveDiet(dietId: number) {
  return authFetch(`/diets/${dietId}/approve`, { method: "POST" }).then((r) =>
    parseJson<Diet>(r),
  )
}

export function discardDiet(dietId: number) {
  return authFetch(`/diets/${dietId}/discard`, { method: "POST" }).then((r) =>
    parseJson<Diet>(r),
  )
}

export function quickAdjustDiet(dietId: number, adjustment: string) {
  return authFetch(`/diets/${dietId}/quick-adjust`, {
    method: "POST",
    body: JSON.stringify({ adjustment }),
  }).then((r) => parseJson<Diet>(r))
}

export function updateDietMeals(
  dietId: number,
  body: { meals: { day_index: number; slot_key: string; meal_text: string }[] },
) {
  return authFetch(`/diets/${dietId}/meals`, {
    method: "PATCH",
    body: JSON.stringify(body),
  }).then((r) => parseJson<Diet>(r))
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/services/api.ts
git commit -m "feat: add approveDiet, discardDiet, quickAdjustDiet, updateDietMeals API functions"
```

### Task 3.4: Componentes del wizard (pasos individuales)

**Files:**
- Create: `frontend/src/components/wizard/WizardContainer.tsx`
- Create: `frontend/src/components/wizard/PatientSearchInput.tsx`
- Create: `frontend/src/components/wizard/WizardNoteStep.tsx`
- Create: `frontend/src/components/wizard/DurationPresets.tsx`
- Create: `frontend/src/components/wizard/MealCountSelector.tsx`
- Create: `frontend/src/components/wizard/StrategyModeCards.tsx`
- Create: `frontend/src/components/wizard/DietStyleCards.tsx`
- Create: `frontend/src/components/wizard/MacroPreferences.tsx`
- Create: `frontend/src/components/wizard/ManualTargets.tsx`
- Create: `frontend/src/components/wizard/WizardNavigation.tsx`
- Create: `frontend/src/components/wizard/WizardConfirm.tsx`

Debido a la extensión del plan, estos componentes siguen el mismo patrón Tailwind + tipos definidos en Task 3.1. Cada componente recibe props del estado del wizard y emite acciones via callbacks. Ver el plan completo en el archivo para los detalles de cada componente.

- [ ] **Step 1: WizardContainer.tsx**

```typescript
import type { ReactNode } from "react"
import Stepper from "../ui/Stepper"
import { WIZARD_STEPS, type WizardStep } from "../../types"

type WizardContainerProps = { current: WizardStep; children: ReactNode; title: string }

export default function WizardContainer({ current, children, title }: WizardContainerProps) {
  const stepIndex = WIZARD_STEPS.findIndex((s) => s.key === current)
  const visibleSteps = WIZARD_STEPS.filter((s) => s.key !== "guided_style" && s.key !== "guided_macros" && s.key !== "manual_targets")

  return (
    <div className="mx-auto w-full max-w-lg">
      <h1 className="mb-4 text-xl font-bold text-gray-800">{title}</h1>
      <div className="mb-6">
        <Stepper steps={visibleSteps} current={stepIndex >= 0 ? stepIndex : 0} />
      </div>
      <div className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm md:p-6">
        {children}
      </div>
    </div>
  )
}
```

- [ ] **Step 2-11: Resto de componentes del wizard**

(Siguiendo el mismo patrón: cada componente es un presentational component con Tailwind que recibe `value`, `onChange`, y `onNext`/`onBack` callbacks. Por brevedad del plan, se implementan secuencialmente en este orden.)

- [ ] **Step 12: Commit**

```bash
git add frontend/src/components/wizard/
git commit -m "feat: add wizard step components (patient, note, duration, meals, strategy, guided, manual, confirm, navigation)"
```

### Task 3.5: DietPreviewPanel + DietActions (compartidos)

**Files:**
- Create: `frontend/src/components/diet/NutritionSummary.tsx`
- Create: `frontend/src/components/diet/MealDayAccordion.tsx`
- Create: `frontend/src/components/diet/MealCard.tsx`
- Create: `frontend/src/components/diet/DietActions.tsx`
- Create: `frontend/src/components/diet/QuickAdjustMenu.tsx`
- Create: `frontend/src/components/diet/DietPreviewPanel.tsx`

Estos componentes renderizan la vista previa de la dieta usando los datos de `structured_plan_json` del `Diet`. Usan Tailwind para diseño responsive (stacked en mobile, grid en desktop).

- [ ] **Step 1-6: Implementar cada componente**

- [ ] **Step 7: Commit**

```bash
git add frontend/src/components/diet/
git commit -m "feat: add diet preview panel, nutrition summary, meal accordion, actions, quick-adjust"
```

### Task 3.6: Página DietWizard (orquestador)

**Files:**
- Create: `frontend/src/pages/DietWizard.tsx`
- Modify: `frontend/src/App.tsx`

- [ ] **Step 1: DietWizard.tsx — orquestador del wizard**

```typescript
import { useReducer, useState, useCallback } from "react"
import { useNavigate, useSearchParams } from "react-router-dom"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { wizardReducer, initialWizardState, type WizardStep } from "../types"
import { useDietGeneration } from "../hooks/useDietGeneration"
import WizardContainer from "../components/wizard/WizardContainer"
import PatientSearchInput from "../components/wizard/PatientSearchInput"
import WizardNoteStep from "../components/wizard/WizardNoteStep"
import DurationPresets from "../components/wizard/DurationPresets"
import MealCountSelector from "../components/wizard/MealCountSelector"
import StrategyModeCards from "../components/wizard/StrategyModeCards"
import DietStyleCards from "../components/wizard/DietStyleCards"
import MacroPreferences from "../components/wizard/MacroPreferences"
import ManualTargets from "../components/wizard/ManualTargets"
import WizardConfirm from "../components/wizard/WizardConfirm"
import WizardNavigation from "../components/wizard/WizardNavigation"
import DietPreviewPanel from "../components/diet/DietPreviewPanel"
import type { DietGenerateRequest, DietStrategyMode, MealsPerDay } from "../types"

const queryClient = new QueryClient()

function DietWizardInner() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const patientParam = searchParams.get("patient")
  const initialPatientId = patientParam ? Number(patientParam) : undefined

  const [state, dispatch] = useReducer(
    wizardReducer,
    initialWizardState(initialPatientId),
  )
  const [step, setStep] = useState<WizardStep>(initialPatientId ? "note" : "patient")
  const { generate } = useDietGeneration()

  const buildBody = useCallback((): DietGenerateRequest => {
    const body: DietGenerateRequest = {
      patient_id: state.patientId!,
      duration_days: state.durationDays,
      meals_per_day: state.mealsPerDay as MealsPerDay,
      strategy_mode: state.strategyMode as DietStrategyMode,
    }
    if (state.doctorInstruction.trim()) {
      body.doctor_instruction = state.doctorInstruction.trim()
    }
    if (state.strategyMode === "guided") {
      if (state.dietStyle) body.diet_style = state.dietStyle
      const macro: Record<string, string> = {}
      if (state.macroProtein) macro.protein = state.macroProtein
      if (state.macroCarbs) macro.carbs = state.macroCarbs
      if (state.macroFat) macro.fat = state.macroFat
      if (Object.keys(macro).length) body.macro_mode = macro as DietGenerateRequest["macro_mode"]
    }
    if (state.strategyMode === "manual") {
      const mt: Record<string, number> = {}
      if (state.manualKcal) mt.daily_calories = Number(state.manualKcal)
      if (state.manualProteinG) mt.protein_g = Number(state.manualProteinG)
      if (state.manualCarbsG) mt.carbs_g = Number(state.manualCarbsG)
      if (state.manualFatG) mt.fat_g = Number(state.manualFatG)
      if (Object.keys(mt).length) body.manual_targets = mt as DietGenerateRequest["manual_targets"]
    }
    return body
  }, [state])

  const handleGenerate = async () => {
    const body = buildBody()
    const result = await generate.mutateAsync({ ...body } as Parameters<typeof generate.mutate>[0])
    dispatch({ type: "SET_DIET", diet: result })
    setStep("preview")
  }

  const stepOrder: WizardStep[] = ["patient", "note", "duration", "meals", "strategy", "confirm", "preview"]
  const currentIndex = stepOrder.indexOf(step)

  const goNext = () => {
    if (currentIndex < stepOrder.length - 1) {
      const next = stepOrder[currentIndex + 1]
      if (next === "confirm" && state.strategyMode === "guided") {
        setStep("guided_style")
      } else if (next === "confirm" && state.strategyMode === "manual") {
        setStep("manual_targets")
      } else {
        setStep(next)
      }
    }
  }

  const goBack = () => {
    if (currentIndex > 0) setStep(stepOrder[currentIndex - 1])
  }

  const renderStep = () => {
    switch (step) {
      case "patient":
        return (
          <PatientSearchInput
            onSelect={(patient) => {
              dispatch({ type: "SET_FIELD", field: "patientId", value: patient.id })
              dispatch({ type: "SET_FIELD", field: "patientName", value: `${patient.first_name} ${patient.last_name}` })
              goNext()
            }}
          />
        )
      case "note":
        return (
          <WizardNoteStep
            value={state.doctorInstruction}
            onChange={(v) => dispatch({ type: "SET_FIELD", field: "doctorInstruction", value: v })}
            onSkip={goNext}
          />
        )
      case "duration":
        return (
          <DurationPresets
            value={state.durationDays}
            onChange={(v) => dispatch({ type: "SET_FIELD", field: "durationDays", value: v })}
          />
        )
      case "meals":
        return (
          <MealCountSelector
            value={state.mealsPerDay}
            onChange={(v) => dispatch({ type: "SET_FIELD", field: "mealsPerDay", value: v })}
          />
        )
      case "strategy":
        return (
          <StrategyModeCards
            value={state.strategyMode}
            onChange={(v) => dispatch({ type: "SET_FIELD", field: "strategyMode", value: v })}
          />
        )
      case "guided_style":
        return (
          <DietStyleCards
            value={state.dietStyle}
            onChange={(v) => dispatch({ type: "SET_FIELD", field: "dietStyle", value: v })}
            onNext={() => setStep("guided_macros")}
          />
        )
      case "guided_macros":
        return (
          <MacroPreferences
            protein={state.macroProtein}
            carbs={state.macroCarbs}
            fat={state.macroFat}
            onChange={(field, v) => dispatch({ type: "SET_FIELD", field, value: v })}
            onNext={() => setStep("confirm")}
          />
        )
      case "manual_targets":
        return (
          <ManualTargets
            kcal={state.manualKcal}
            protein={state.manualProteinG}
            carbs={state.manualCarbsG}
            fat={state.manualFatG}
            onChange={(field, v) => dispatch({ type: "SET_FIELD", field, value: v })}
            onNext={() => setStep("confirm")}
          />
        )
      case "confirm":
        return <WizardConfirm state={state} onGenerate={handleGenerate} loading={generate.isPending} />
      case "preview":
        return state.generatedDiet ? (
          <DietPreviewPanel diet={state.generatedDiet} />
        ) : null
      default:
        return null
    }
  }

  return (
    <WizardContainer current={step} title={state.isRegeneration ? "Regenerar Dieta" : "Nueva Dieta"}>
      {renderStep()}

      {generate.isError && (
        <div className="mt-4 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">
          {(generate.error as Error)?.message || "Error al generar la dieta"}
        </div>
      )}

      <WizardNavigation
        step={step}
        onBack={goBack}
        onNext={goNext}
        hideNext={["patient", "confirm", "preview"].includes(step)}
        disableNext={step === "patient" && !state.patientId}
      />
    </WizardContainer>
  )
}

export default function DietWizard() {
  return (
    <QueryClientProvider client={queryClient}>
      <DietWizardInner />
    </QueryClientProvider>
  )
}
```

- [ ] **Step 2: Agregar rutas en App.tsx**

```typescript
import DietWizard from "./pages/DietWizard"

// Dentro del Route de AdminLayout:
<Route path="diets/new" element={<DietWizard />} />
<Route path="diets/:dietId/regenerate" element={<DietWizard />} />
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/pages/DietWizard.tsx frontend/src/App.tsx
git commit -m "feat: add DietWizard page with 7-step wizard and TanStack Query"
```

---

## Fase 4: Compartir Links (Día 11-12)

### Task 4.1: Componente ShareButtons

**Files:**
- Create: `frontend/src/components/ShareButtons.tsx`

- [ ] **Step 1: ShareButtons.tsx — WhatsApp + Email + Copiar**

```typescript
import { useState } from "react"
import Button from "./ui/Button"

type ShareButtonsProps = {
  url: string
  patientName: string
  type: "register" | "update"
}

const MESSAGES: Record<"register" | "update", { wa: string; emailSubject: string; emailBody: string }> = {
  register: {
    wa: "Hola%2C%20la%20Dra.%20Acosta%20te%20invita%20a%20completar%20tu%20ficha%20nutricional%20para%20tu%20plan%20personalizado%3A",
    emailSubject: "Completa tu ficha nutricional - Dra. Acosta",
    emailBody: "Hola,%0D%0A%0D%0ALa Dra. Acosta te comparte este link para que completes tu información nutricional y así preparar tu plan personalizado:%0D%0A%0D%0A",
  },
  update: {
    wa: "Hola%2C%20la%20Dra.%20Acosta%20te%20comparte%20este%20link%20para%20actualizar%20tus%20datos%20nutricionales%3A",
    emailSubject: "Actualiza tus datos nutricionales - Dra. Acosta",
    emailBody: "Hola,%0D%0A%0D%0ALa Dra. Acosta te comparte este link para que actualices tus datos (peso, medidas, hábitos) y ajustar tu plan nutricional:%0D%0A%0D%0A",
  },
}

export default function ShareButtons({ url, patientName, type }: ShareButtonsProps) {
  const [copied, setCopied] = useState(false)
  const msg = MESSAGES[type]

  const waLink = `https://wa.me/?text=${msg.wa}%0A%0A${encodeURIComponent(url)}`
  const emailLink = `mailto:?subject=${encodeURIComponent(msg.emailSubject)}&body=${msg.emailBody}${encodeURIComponent(url)}`

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(url)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      // Fallback para entornos sin clipboard API
      const input = document.createElement("input")
      input.value = url
      document.body.appendChild(input)
      input.select()
      document.execCommand("copy")
      document.body.removeChild(input)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  return (
    <div className="space-y-3">
      {/* URL display */}
      <div className="flex items-center gap-2 rounded-lg border border-gray-200 bg-gray-50 px-3 py-2">
        <input
          type="text"
          readOnly
          value={url}
          className="flex-1 bg-transparent text-sm text-gray-600 truncate outline-none"
        />
        <button
          type="button"
          onClick={handleCopy}
          className="shrink-0 rounded-md px-2 py-1 text-xs font-medium text-gray-500 hover:bg-gray-200 transition-colors"
        >
          {copied ? "✓ Copiado" : "📋 Copiar"}
        </button>
      </div>

      {/* Share buttons */}
      <div className="flex gap-2">
        <a
          href={waLink}
          target="_blank"
          rel="noopener noreferrer"
          className="flex flex-1 items-center justify-center gap-2 rounded-lg bg-green-500 px-4 py-2.5 text-sm font-medium text-white hover:bg-green-600 transition-colors shadow-sm"
        >
          📱 WhatsApp
        </a>
        <a
          href={emailLink}
          className="flex flex-1 items-center justify-center gap-2 rounded-lg bg-gray-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-gray-700 transition-colors shadow-sm"
        >
          📧 Correo
        </a>
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/ShareButtons.tsx
git commit -m "feat: add ShareButtons component (WhatsApp + Email + Copy)"
```

### Task 4.2: Integrar ShareButtons en IntakeLinks (panel)

**Files:**
- Modify: `frontend/src/pages/IntakeLinks.tsx`

- [ ] **Step 1: Agregar ShareButtons al crear un link**

Modificar `IntakeLinks.tsx` para que después de crear un link exitoso, muestre `ShareButtons` debajo con la URL generada.

```typescript
import ShareButtons from "../components/ShareButtons"

// En la sección de creación de link, después de link creado:
const frontendBase = import.meta.env.VITE_FRONTEND_URL || window.location.origin
const intakeUrl = `${frontendBase}/intake/${newLink.token}`

// Mostrar debajo del formulario:
{intakeUrl && (
  <div className="mt-4">
    <ShareButtons
      url={intakeUrl}
      patientName={selectedPatientName}
      type={linkType} // "register" o "update"
    />
  </div>
)}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/pages/IntakeLinks.tsx
git commit -m "feat: integrate ShareButtons into IntakeLinks page"
```

---

## Fase 5: Vista Previa y Aprobación en DietDetail (Día 13)

### Task 5.1: Refactorizar DietDetail para usar DietPreviewPanel + acciones

**Files:**
- Modify: `frontend/src/pages/DietDetail.tsx`

- [ ] **Step 1: Integrar DietPreviewPanel + DietActions en DietDetail**

Reemplazar la sección de visualización del plan en `DietDetail.tsx` con `<DietPreviewPanel diet={diet} />` y agregar `<DietActions dietId={diet.id} status={diet.status} onRefresh={refetch} />` para mostrar botones contextuales (Aprobar/Descartar si pending_approval, PDF/Regenerar si generated).

- [ ] **Step 2: Commit**

```bash
git add frontend/src/pages/DietDetail.tsx
git commit -m "feat: refactor DietDetail to use shared DietPreviewPanel and DietActions"
```

---

## Fase 6: Corte Directo y Limpieza Telegram (Día 14-15)

### Task 6.1: Feature flag en backend

**Files:**
- Modify: `backend/app/core/config.py`

- [ ] **Step 1: Agregar TELEGRAM_ENABLED**

```python
TELEGRAM_ENABLED: bool = True
```

- [ ] **Step 2: Guardar webhook con feature flag**

En `backend/app/api/telegram.py`, en la función del webhook:
```python
if not settings.TELEGRAM_ENABLED:
    return {"ok": True}
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/core/config.py backend/app/api/telegram.py
git commit -m "feat: add TELEGRAM_ENABLED feature flag for graceful shutdown"
```

### Task 6.2: Archivar código Telegram y limpiar modelos

- [ ] **Step 1: Mover archivos Telegram a _archive/**

```bash
cd "/home/hendrick-rafael/Desktop/Proyectos Oficiales/diet_telegram_agent/backend"
mkdir -p app/services/_archive app/api/_archive

git mv app/services/telegram_handler.py app/services/_archive/
git mv app/services/telegram_diet_messages.py app/services/_archive/
git mv app/services/telegram_diet_strategy.py app/services/_archive/
git mv app/services/telegram_diet_ui.py app/services/_archive/
git mv app/services/telegram_client.py app/services/_archive/
git mv app/services/telegram_intent_service.py app/services/_archive/
git mv app/api/telegram.py app/api/_archive/
```

- [ ] **Step 2: Crear migración Alembic para eliminar tablas Telegram**

```bash
cd backend
alembic revision -m "0007_remove_telegram_tables"
```

En el migration file:
```python
def upgrade():
    op.drop_table("conversation_states")
    op.drop_table("doctor_telegram_bindings")
    op.drop_table("telegram_pending_links")
    op.drop_table("telegram_processed_updates")
    op.drop_column("doctors", "telegram_user_id")
    op.drop_column("doctors", "telegram_username")

def downgrade():
    # recrear tablas si se necesita rollback
    pass
```

- [ ] **Step 3: Eliminar tests Telegram**

```bash
cd backend
git rm tests/test_telegram_*.py
```

- [ ] **Step 4: Actualizar requirements.txt**

Remover `python-telegram-bot` si existe en requirements.txt

- [ ] **Step 5: Commit final**

```bash
git add -A
git commit -m "feat: archive Telegram code, drop Telegram tables, remove Telegram tests"
```

---

## Verificación Final

```bash
# Backend
cd backend
pytest -q  # todos los tests pasan
alembic upgrade head  # migración limpia

# Frontend
cd frontend
npm run typecheck  # sin errores
npm run lint       # sin errores
npm run build      # dist/ generado con service worker

# E2E manual
# 1. Login con logo → OK
# 2. Navegar sidebar responsive → OK
# 3. Wizard nueva dieta → preview → aprobar → PDF → OK
# 4. Crear link de registro → compartir WhatsApp → OK
# 5. Crear link de actualización → compartir Email → OK
# 6. DietDetail con botones aprobar/descartar → OK
# 7. Mobile (Chrome DevTools) → responsive + instalable → OK
```
