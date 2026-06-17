# Reestructuración del Intake Público y Recordatorios Automáticos

**Fecha:** 2026-06-16
**Estado:** Design approved

---

## Resumen

Separar el formulario de intake público en dos momentos: lo que llena el paciente (solo datos personales + preferencias alimentarias) y lo que llena el doctor en consulta (medidas, historial clínico, perfil nutricional, estilo de vida). Además, integrar el sistema de recordatorios automáticos por email a los 30 días con la lógica de pacientes sin email.

---

## 1. Formulario del Paciente (Registro Público)

El paciente llena **10 campos**. Sin datos clínicos, sin medidas corporales.

| # | Campo | Tipo | Requerido | Notas |
|---|-------|------|-----------|-------|
| 1 | `first_name` | texto | Sí | |
| 2 | `last_name` | texto | Sí | |
| 3 | `birth_date` | date | Sí | |
| 4 | `sex` | texto | Sí | |
| 5 | `email` | email | No | Label informativo no-intrusivo |
| 6 | `whatsapp` | tel | No | Label informativo no-intrusivo |
| 7 | `country` | dropdown búsqueda | Sí | API externa, español, jerárquico |
| 8 | `city` | dropdown búsqueda | Sí | Filtrado por país |
| 9 | `objective` | select | Sí | Mismos valores actuales |
| 10 | `disliked_foods` | textarea | Sí | "¿Qué alimentos NO te gustas o NO consumes?" |

### Label de contacto

Texto informativo debajo de email y WhatsApp:

> "El correo y WhatsApp nos ayudan a mantenerte al día con recordatorios y actualizaciones de tu plan."

Estilo: fondo `#f1f5f9`, texto `#64748b`, borde redondeado. No obstructivo.

### Selector de País/Ciudad

- API externa (REST Countries + GeoNames o similar)
- Dropdown con barra de búsqueda textual
- Nombres en español
- Jerárquico: al seleccionar un país, se cargan solo las ciudades de ese país
- Valor por defecto: República Dominicana

---

## 2. Formulario del Doctor (Panel de Administración)

El doctor completa **26 campos** en el detalle del paciente dentro del panel de administración.

### 2.1 Medidas Corporales

| Campo | Tipo | Requerido |
|-------|------|-----------|
| `weight_kg` | float | Sí |
| `height_cm` | float | Sí |
| `neck_cm` | float | No |
| `chest_cm` | float | No |
| `waist_cm` | float | No |
| `hip_cm` | float | No |
| `leg_cm` | float | No |
| `calf_cm` | float | No |

### 2.2 Historial Clínico

| Campo | Tipo | Requerido |
|-------|------|-----------|
| `diseases` | textarea | No |
| `medications` | textarea | No |
| `medical_history` | textarea | No |
| `food_allergies` | textarea | Sí |

### 2.3 Perfil Nutricional

| Campo | Tipo | Requerido |
|-------|------|-----------|
| `dietary_style` | texto | No |
| `food_preferences` | textarea | No |
| `foods_avoided` | textarea | No |
| `water_intake_liters` | float | No |
| `meal_schedule` | textarea / JSON | No |

### 2.4 Estilo de Vida

| Campo | Tipo | Requerido |
|-------|------|-----------|
| `activity_level` | texto | No |
| `stress_level` | integer (1-5) | No |
| `sleep_quality` | integer (1-5) | No |
| `sleep_hours` | float | No |
| `exercise_frequency_per_week` | integer (0-7) | No |
| `exercise_type` | texto | No |
| `budget_level` | texto | No |
| `adherence_level` | integer (1-5) | No |
| `extra_notes` | textarea | No |

Los campos de estilo de vida que el doctor no alcanzó a preguntar quedan como `null`/opcional. No bloquear la generación de la dieta por falta de estos campos.

---

## 3. Flujo de Actualización (30 días)

### 3.1 Condiciones

- Si el paciente **tiene email**: el scheduler envía recordatorio automático a los 30 días
- Si el paciente **NO tiene email**: el scheduler salta ese paciente. La doctora lo maneja en consulta presencial

### 3.2 Email Recordatorio

Mismo diseño y lógica del plan original:
- Template HTML con logo de la Dra. Acosta
- Botón "Actualizar mis datos" con link de un solo uso (expira 7 días)
- Envío vía Gmail API (httpx)
- Controlado por flag `REMINDER_ENABLED` en `.env`

### 3.3 Pantalla de Actualización (Update Mode)

Se reusa el modo "update" existente de `PublicIntake.tsx`, agregando país y ciudad.

**Campos visibles en update:**
- `first_name`, `last_name`
- `whatsapp`
- `country` *, `city` *
- `weight_kg` *

**Campos ocultos / no editables en update:**
- `email` (no se puede cambiar, es el identificador de contacto)
- `birth_date`, `sex`
- `objective`, `disliked_foods`
- Todo lo clínico (es competencia del doctor)
- `height_cm` (no cambia en adultos)
- Perímetros corporales

---

## 4. Arquitectura General

```
                    Público (paciente)                        Privado (doctor)
                    ──────────────────                        ────────────────

Registro:           PublicIntake.tsx                          Admin panel:
┌─ Datos personales  →  PatientCreate schema                  ┌─ Medidas
├─ Contacto (opt)    →                                     ├─ Historial clínico
├─ País/Ciudad (API)  →                                     ├─ Perfil nutricional
├─ Objetivo          →                                     └─ Estilo de vida
└─ disliked_foods    →                                          │
       │                                                         │
       ▼                                                         ▼
┌─────────────────────────────┐                    ┌─────────────────────────┐
│ IntakeLink submit           │                    │ DoctorProfileUpdate     │
│ (crea Patient + Profile +   │                    │ (solo el doctor puede   │
│  Metrics vacío)             │                    │  editar estos campos)   │
└──────────┬──────────────────┘                    └─────────────────────────┘
           │
           ▼
┌──────────────────────────────────────────────────────────────────────┐
│ 30 días después                                                     │
│                                                                     │
│ ¿Tiene email? ──Sí──→ Email con link de update (peso, país, ciudad)│
│      │                                                              │
│      No                                                             │
│      ▼                                                              │
│ Doctor pregunta en consulta                                         │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 5. Cambios técnicos necesarios

### Backend

| Archivo | Cambio |
|---------|--------|
| `backend/app/schemas.py` | `IntakePublicSubmit`: quitar `food_allergies`, `foods_avoided`, `weight_kg`, `height_cm` y medidas corporales del schema de registro. Hacer `email` opcional |
| `backend/app/schemas.py` | `IntakeUpdateSubmit`: agregar `country`, `city`. Quitar `email` |
| `backend/app/schemas.py` | Nuevo schema `DoctorProfileUpsert` con todos los campos clínicos incluyendo `food_allergies` |
| `backend/app/models.py` | Sin cambios al esquema (ya existe todo) |
| `backend/app/api/intake_links.py` | `public_submit`: no crear `PatientMetrics` automáticamente. Crear perfil sin datos clínicos |
| `backend/app/api/intake_links.py` | `public_update`: agregar `country`, `city` a la actualización |
| `backend/app/api/` | Nuevo endpoint `PUT /api/doctors/patients/{id}/profile` para que el doctor guarde datos clínicos |
| `backend/app/services/email_service.py` | Sin cambios (ya implementado) |
| `backend/app/services/reminder_service.py` | Sin cambios (ya implementado) |
| `backend/app/main.py` | Sin cambios (ya implementado) |

### Frontend

| Archivo | Cambio |
|---------|--------|
| `frontend/src/pages/PublicIntake.tsx` | Modo registro: ocultar sección de medidas, historial clínico, hábitos. Agregar label informativo en email/whatsapp. Agregar selector país/ciudad con búsqueda |
| `frontend/src/pages/PublicIntake.tsx` | Modo update: agregar país/ciudad. Quitar email |
| `frontend/src/services/api.ts` | Agregar endpoint `updateDoctorProfile(patientId, data)` |
| `frontend/src/` | Nuevo componente `LocationSelector` con dropdown de país/ciudad con búsqueda |
| `frontend/src/` | Nueva página/sección en admin panel para el formulario del doctor |
| `frontend/src/` | Agregar dependencia para API de países/ciudades (ej: `react-select` + API) |

### API de País/Ciudad

Se necesita una API que:
- Devuelva países y ciudades en español
- Permita búsqueda textual
- Sea gratuita o de bajo costo

Opciones a evaluar:
- **REST Countries** (`https://restcountries.com`) — países en español ✅
- **GeoNames** — ciudades con búsqueda, requiere API key gratuita
- **CountryStateCity API** (`https://api.countrystatecity.in`) — completa, gratis con rate limits

---

## 6. Flujo completo paso a paso

### Día 0: Registro del paciente

1. Paciente abre link de intake público
2. Llena: nombre, apellido, fecha nacimiento, sexo, email (opc), whatsapp (opc), país, ciudad, objetivo, disliked_foods
3. Envía el formulario
4. Backend crea `Patient`, `PatientProfile` (con solo esos campos), **no crea `PatientMetrics`**
5. Queda pendiente: el doctor debe completar la ficha clínica

### Consulta (día variable)

1. Doctor abre el perfil del paciente en el admin panel
2. Ve un indicador: "Pendiente de evaluación clínica"
3. Llena medidas corporales, historial clínico (incluyendo alergias), perfil nutricional, estilo de vida
4. Guarda y genera la dieta

### Día 30

1. El scheduler (`APScheduler`) corre `check_and_send_reminders()`
2. Para cada dieta con ≥30 días:
   - ¿Paciente tiene email? → envía recordatorio automático con link para actualizar peso/país/ciudad
   - ¿No tiene email? → lo salta, el doctor lo maneja en consulta
3. Link de actualización es de un solo uso, expira en 7 días

---

## 7. No-Alcance (para mantener foco)

- No se cambia el motor de generación de dietas
- No se modifican los formatos de email existentes
- No se agregan notificaciones al doctor (push, SMS)
- No se modifica el login de la doctora
- No se manejan múltiples idiomas en el selector de país/ciudad
