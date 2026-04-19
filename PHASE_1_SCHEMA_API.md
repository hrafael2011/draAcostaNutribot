# Fase 1 - Schema y API

## Objetivo de la Fase 1

Definir con precision:
- Tablas base del nuevo sistema
- Relaciones entre entidades
- Endpoints iniciales del panel admin
- Endpoints del formulario por link
- Estructura minima para dejar listo el proyecto

Esta fase no implementa aun el bot completo de Telegram ni la generacion final de dieta. Deja lista la base para construirlas.

## Base Tecnica

- Backend: FastAPI
- ORM: SQLAlchemy
- Migraciones: Alembic
- DB: PostgreSQL
- Cache y colas: Redis
- Frontend admin: React + TypeScript + Vite

## Tablas Exactas

### 1. doctors

Representa a la doctora propietaria del espacio de trabajo.

Campos:
- `id` bigint pk
- `full_name` varchar(160) not null
- `email` varchar(190) unique not null
- `phone` varchar(30) null
- `hashed_password` varchar(255) not null
- `telegram_user_id` varchar(40) unique null
- `telegram_username` varchar(120) null
- `is_active` boolean default true
- `created_at` timestamptz not null
- `updated_at` timestamptz not null

Notas:
- Para el MVP, una doctora es equivalente al owner del sistema.
- El binding directo con Telegram puede vivir aqui y tambien auditarse en tabla separada.

### 2. doctor_telegram_bindings

Relaciona doctora con su cuenta de Telegram.

Campos:
- `id` bigint pk
- `doctor_id` bigint fk -> doctors.id
- `telegram_user_id` varchar(40) unique not null
- `telegram_chat_id` varchar(40) unique not null
- `telegram_username` varchar(120) null
- `is_active` boolean default true
- `created_at` timestamptz not null
- `updated_at` timestamptz not null

Notas:
- Se usara para validar que solo la doctora autorizada opere el agente.

### 3. patients

Entidad principal del paciente.

Campos:
- `id` bigint pk
- `doctor_id` bigint fk -> doctors.id
- `first_name` varchar(120) not null
- `last_name` varchar(120) not null
- `birth_date` date null
- `sex` varchar(20) null
- `whatsapp` varchar(30) null
- `email` varchar(190) null
- `country` varchar(120) null
- `city` varchar(120) null
- `source` varchar(20) not null default `admin`
- `is_active` boolean default true
- `is_archived` boolean default false
- `created_at` timestamptz not null
- `updated_at` timestamptz not null

Valores sugeridos de `source`:
- `admin`
- `intake_link`
- `telegram`

### 4. patient_profiles

Informacion clinica y nutricional actual del paciente.

Campos:
- `id` bigint pk
- `patient_id` bigint unique fk -> patients.id
- `objective` varchar(80) null
- `diseases` text null
- `medications` text null
- `food_allergies` text null
- `foods_avoided` text null
- `medical_history` text null
- `dietary_style` varchar(80) null
- `food_preferences` text null
- `disliked_foods` text null
- `meal_schedule` jsonb null
- `water_intake_liters` numeric(5,2) null
- `activity_level` varchar(20) null
- `stress_level` smallint null
- `sleep_quality` smallint null
- `sleep_hours` numeric(4,2) null
- `budget_level` varchar(20) null
- `adherence_level` smallint null
- `exercise_frequency_per_week` smallint null
- `exercise_type` text null
- `extra_notes` text null
- `completed_by_patient` boolean default false
- `completed_at` timestamptz null
- `created_at` timestamptz not null
- `updated_at` timestamptz not null

Restricciones sugeridas:
- `stress_level` entre 1 y 5
- `sleep_quality` entre 1 y 5
- `adherence_level` entre 1 y 5

Valores sugeridos:
- `activity_level`: `very_low`, `low`, `moderate`, `high`, `very_high`
- `budget_level`: `very_tight`, `low`, `medium`, `medium_high`, `flexible`

### 5. patient_metrics

Historial de medidas y peso.

Campos:
- `id` bigint pk
- `patient_id` bigint fk -> patients.id
- `weight_kg` numeric(6,2) null
- `height_cm` numeric(6,2) null
- `neck_cm` numeric(6,2) null
- `chest_cm` numeric(6,2) null
- `waist_cm` numeric(6,2) null
- `hip_cm` numeric(6,2) null
- `leg_cm` numeric(6,2) null
- `calf_cm` numeric(6,2) null
- `recorded_at` timestamptz not null
- `source` varchar(20) not null default `admin`
- `notes` text null
- `created_at` timestamptz not null

Notas:
- Esta tabla guarda historial.
- Para la ficha actual se toma el ultimo registro.

### 6. patient_intake_links

Links unicos para que el paciente llene su formulario.

Campos:
- `id` bigint pk
- `doctor_id` bigint fk -> doctors.id
- `patient_id` bigint fk -> patients.id
- `token` varchar(80) unique not null
- `status` varchar(20) not null default `active`
- `expires_at` timestamptz not null
- `max_uses` integer not null default 1
- `use_count` integer not null default 0
- `last_used_at` timestamptz null
- `created_at` timestamptz not null
- `updated_at` timestamptz not null

Valores sugeridos de `status`:
- `active`
- `completed`
- `expired`
- `revoked`

### 7. diets

Registro principal de dieta generada para un paciente.

Campos:
- `id` bigint pk
- `patient_id` bigint fk -> patients.id
- `doctor_id` bigint fk -> doctors.id
- `status` varchar(20) not null default `draft`
- `title` varchar(160) null
- `summary` text null
- `structured_plan_json` jsonb not null
- `pdf_file_path` varchar(255) null
- `notes` text null
- `created_at` timestamptz not null
- `updated_at` timestamptz not null

Valores sugeridos de `status`:
- `draft`
- `generated`
- `approved`
- `archived`

### 8. diet_versions

Versionado de cada dieta y de cada regeneracion.

Campos:
- `id` bigint pk
- `diet_id` bigint fk -> diets.id
- `version_number` integer not null
- `doctor_instruction` text null
- `input_snapshot_json` jsonb not null
- `output_json` jsonb not null
- `pdf_file_path` varchar(255) null
- `created_at` timestamptz not null

### 9. conversation_states

Estado de conversacion con la doctora por Telegram.

Campos:
- `id` bigint pk
- `doctor_id` bigint fk -> doctors.id
- `channel_user_key` varchar(80) not null
- `context_data` jsonb not null
- `updated_at` timestamptz not null

Indice sugerido:
- unique (`doctor_id`, `channel_user_key`)

### 10. audit_logs

Bitacora de cambios importantes del sistema.

Campos:
- `id` bigint pk
- `doctor_id` bigint fk -> doctors.id
- `action` varchar(80) not null
- `entity_type` varchar(80) not null
- `entity_id` bigint null
- `payload_json` jsonb null
- `created_at` timestamptz not null

## Relaciones

- Un `doctor` tiene muchos `patients`
- Un `patient` tiene un `patient_profile`
- Un `patient` tiene muchos `patient_metrics`
- Un `patient` puede tener muchos `patient_intake_links`
- Un `patient` puede tener muchas `diets`
- Una `diet` tiene muchas `diet_versions`
- Un `doctor` puede tener un binding principal en `doctor_telegram_bindings`
- Un `doctor` puede tener muchos `audit_logs`

## Endpoints Exactos MVP

Prefijo base recomendado:
- `/api/auth`
- `/api/doctors`
- `/api/patients`
- `/api/intake-links`
- `/api/diets`
- `/api/telegram`
- `/api/dashboard`

### Auth

#### POST `/api/auth/register`
Crear cuenta de doctora.

Body:
```json
{
  "full_name": "Dra. Ana Perez",
  "email": "ana@example.com",
  "password": "secret123",
  "phone": "+18095550000"
}
```

#### POST `/api/auth/token`
Login.

#### POST `/api/auth/refresh`
Refresh token.

#### POST `/api/auth/logout`
Cerrar sesion.

### Doctors

#### GET `/api/doctors/me`
Obtener perfil actual de la doctora.

#### PATCH `/api/doctors/me`
Actualizar perfil.

Body ejemplo:
```json
{
  "full_name": "Dra. Ana M. Perez",
  "phone": "+18095550000"
}
```

### Dashboard

#### GET `/api/dashboard/summary`
Resumen del panel.

Response ejemplo:
```json
{
  "total_patients": 30,
  "new_patients_30d": 8,
  "incomplete_profiles": 5,
  "diets_generated": 19,
  "latest_activity": []
}
```

### Patients

#### GET `/api/patients`
Listar pacientes de la doctora.

Query params:
- `search`
- `status`
- `page`
- `page_size`

#### POST `/api/patients`
Crear paciente manualmente desde panel.

Body ejemplo:
```json
{
  "first_name": "Maria",
  "last_name": "Lopez",
  "birth_date": "1991-05-10",
  "sex": "female",
  "whatsapp": "+18095550111",
  "email": "maria@example.com",
  "country": "Republica Dominicana",
  "city": "Santo Domingo"
}
```

#### GET `/api/patients/{patient_id}`
Detalle completo del paciente.

#### PATCH `/api/patients/{patient_id}`
Actualizar datos base del paciente.

#### GET `/api/patients/{patient_id}/profile`
Ver perfil clinico.

#### PUT `/api/patients/{patient_id}/profile`
Crear o reemplazar perfil clinico.

#### PATCH `/api/patients/{patient_id}/profile`
Actualizar parcialmente perfil clinico.

Body ejemplo:
```json
{
  "objective": "lose_weight",
  "diseases": "Hipotiroidismo",
  "food_allergies": "Mani",
  "foods_avoided": "Leche entera, mariscos",
  "stress_level": 4,
  "budget_level": "medium",
  "activity_level": "low"
}
```

#### GET `/api/patients/{patient_id}/metrics`
Listar historial de medidas.

#### POST `/api/patients/{patient_id}/metrics`
Registrar nuevas medidas.

Body ejemplo:
```json
{
  "weight_kg": 74.5,
  "height_cm": 164,
  "waist_cm": 88,
  "hip_cm": 104,
  "source": "admin",
  "notes": "Control de abril"
}
```

#### GET `/api/patients/{patient_id}/summary`
Resumen compacto para usar en Telegram y panel.

Response ejemplo:
```json
{
  "patient": {
    "id": 15,
    "full_name": "Maria Lopez"
  },
  "latest_metrics": {
    "weight_kg": 74.5,
    "height_cm": 164
  },
  "profile_flags": {
    "has_allergies": true,
    "has_diseases": true,
    "is_profile_complete": false
  },
  "latest_diet": {
    "id": 9,
    "created_at": "2026-04-13T18:00:00Z"
  }
}
```

### Intake Links

#### GET `/api/intake-links`
Listar links generados por la doctora.

#### POST `/api/intake-links`
Crear link para un paciente.

Body ejemplo:
```json
{
  "patient_id": 15,
  "expires_in_days": 7,
  "max_uses": 1
}
```

#### POST `/api/intake-links/{link_id}/revoke`
Revocar link.

#### GET `/api/intake-links/public/{token}`
Validar link publico y devolver datos minimos del formulario.

#### POST `/api/intake-links/public/{token}/submit`
Enviar formulario del paciente.

Body ejemplo:
```json
{
  "first_name": "Maria",
  "last_name": "Lopez",
  "birth_date": "1991-05-10",
  "sex": "female",
  "whatsapp": "+18095550111",
  "email": "maria@example.com",
  "country": "Republica Dominicana",
  "city": "Santo Domingo",
  "objective": "lose_weight",
  "diseases": "Hipotiroidismo",
  "medications": "Levotiroxina",
  "food_allergies": "Mani",
  "foods_avoided": "Leche entera",
  "stress_level": 4,
  "sleep_quality": 3,
  "budget_level": "medium",
  "activity_level": "low",
  "weight_kg": 74.5,
  "height_cm": 164
}
```

### Diets

#### GET `/api/diets`
Listar dietas de la doctora.

Query params:
- `patient_id`
- `status`
- `page`
- `page_size`

#### POST `/api/diets/generate`
Generar dieta para un paciente.

Body ejemplo:
```json
{
  "patient_id": 15,
  "doctor_instruction": "Evitar lacteos y usar alimentos economicos"
}
```

#### GET `/api/diets/{diet_id}`
Ver dieta actual.

#### GET `/api/diets/{diet_id}/versions`
Ver historial de versiones.

#### POST `/api/diets/{diet_id}/regenerate`
Regenerar dieta con nuevas instrucciones.

#### GET `/api/diets/{diet_id}/pdf`
Descargar PDF.

### Telegram

#### GET `/api/telegram/binding`
Ver estado de vinculacion de la doctora.

#### POST `/api/telegram/binding/start`
Generar codigo o enlace para vincular Telegram de la doctora.

#### POST `/api/telegram/binding/reset`
Resetear vinculacion.

#### POST `/api/telegram/webhook`
Webhook de Telegram.

## Respuestas Minimas del Formulario Publico

Campos obligatorios sugeridos:
- first_name
- last_name
- birth_date
- sex
- country
- city
- objective
- food_allergies o indicar `none`
- foods_avoided o indicar `none`
- weight_kg
- height_cm

Campos opcionales pero recomendados:
- diseases
- medications
- stress_level
- budget_level
- activity_level
- sleep_quality

## Reglas de Validacion MVP

- No generar dieta si faltan peso, altura, objetivo, sexo o fecha de nacimiento
- Si el paciente no tiene perfil clinico suficiente, marcar `is_profile_complete = false`
- Si un link esta expirado, no debe aceptar submit
- Cada submit de formulario publico debe registrarse en `audit_logs`
- Toda actualizacion desde Telegram debe registrarse en `audit_logs`

## Estructura Minima de Carpetas Recomendada

```text
diet_telegram_agent/
  backend/
    app/
      api/
      core/
      models/
      schemas/
      services/
      prompts/
      handlers/
      utils/
    alembic/
  frontend/
    src/
      pages/
      components/
      services/
      store/
      types/
```

## Cierre de la Fase 1

Al terminar esta fase debe quedar claro:
- Que tablas se van a crear
- Que endpoints va a exponer el sistema
- Cual es la relacion entre panel admin, formulario publico y futuras acciones por Telegram

La siguiente fase construye sobre esta base:
- CRUD real de pacientes
- Links de registro
- Formulario publico funcional
