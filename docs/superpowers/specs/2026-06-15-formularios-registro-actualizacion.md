# Formularios de Registro + Actualización para Pacientes

**Date:** 2026-06-15
**Status:** Design approved

## Context

Actualmente, cuando el doctor comparte un formulario a un paciente, el paciente debe existir previamente en el sistema (creado manualmente por el doctor). No hay forma de que un paciente se registre por sí mismo. Tampoco hay forma de que un paciente existente actualice sus datos por su cuenta.

Se necesita:
1. **Link de registro**: El paciente llena el formulario completo y se crea automáticamente como paciente en el sistema. El doctor no necesita crearlo primero.
2. **Link de actualización**: Un paciente ya registrado recibe un link para modificar solo sus datos personales (nombre, apellido, email, whatsapp, país, ciudad) y medidas (peso, altura). El resto del perfil clínico solo lo modifica el médico.

---

## Feature 1: Link de Registro (Register)

### Modelo de datos

Modificar `PatientIntakeLink` para que `patient_id` sea **nullable** (opcional). Cuando `patient_id IS NULL` y `link_type = "register"`, significa que es un link de registro que creará un paciente al ser enviado.

Agregar campo `link_type` al modelo:
```python
link_type: str  # "register" | "update"
```

### Endpoints

**Crear link de registro:**
`POST /intake-links` con `link_type="register"`
- No requiere `patient_id`
- Crea link con `patient_id=NULL`, `link_type="register"`

**Validar link público:**
`GET /intake-links/public/{token}`
- Devuelve `link_type` en la metadata para que el frontend sepa qué formulario mostrar

**Submit de registro (crear paciente):**
`POST /intake-links/public/{token}/submit`
- Usa `IntakePublicSubmit` (campos requeridos)
- Crea un nuevo `Patient` con los datos del formulario
- Crea `PatientProfile` con todos los datos clínicos
- Crea `PatientMetrics` con peso y altura
- Actualiza el link: asigna `patient_id` al paciente creado, incrementa `use_count`
- Ya existe y funciona, solo hay que adaptarlo para cuando `patient_id` es null

### Frontend

**ShareModal** — Al crear formulario, añadir selector de tipo:
- "📝 Registro" → crea link de registro (sin paciente)
- "🔄 Actualización" → requiere seleccionar paciente existente

**PublicIntake.tsx** — Detectar `link_type`:
- Si es `"register"` → mostrar formulario completo con todos los campos (igual que hoy)
- Si es `"update"` → mostrar formulario simplificado

---

## Feature 2: Link de Actualización (Update)

### Endpoints

**Crear link de actualización:**
`POST /intake-links` con `link_type="update"` y `patient_id`
- Crea link vinculado a un paciente existente

**Submit de actualización:**
`PUT /intake-links/public/{token}/update`
- Usa `IntakeUpdateSubmit` (todos los campos opcionales)
- Solo actualiza: nombre, apellido, email, whatsapp, país, ciudad, peso, altura
- Ya existe el endpoint, hay que limitarlo a solo esos campos

### Formulario simplificado (Update)

Campos que ve el paciente en un link de actualización:

| Campo | Tipo |
|-------|------|
| Nombre | Input texto (pre-llenado) |
| Apellido | Input texto (pre-llenado) |
| Email | Input email (pre-llenado) |
| WhatsApp | Input texto (pre-llenado) |
| País | Select (pre-llenado) |
| Ciudad | Select/Input (pre-llenado) |
| Peso | WeightInput (pre-llenado) |
| Altura | HeightInput (pre-llenado) |

---

## Feature 3: Método de compartir (sin WhatsApp directo)

Los links de formularios se comparten con 3 métodos:

| Método | Móvil | Desktop |
|--------|-------|---------|
| **Compartir** (Web Share API) | ✅ Menú nativo del SO (WhatsApp, Telegram, Gmail, etc.) | ❌ No disponible |
| **Copiar enlace** | ✅ | ✅ |
| **Correo** (mailto:) | ✅ Abre app de correo | ✅ Abre cliente de correo |

- Se elimina el botón directo de WhatsApp (requiere permisos Meta, configuración extra)
- El Web Share API en móvil ya incluye WhatsApp como opción nativa

---

## Archivos a modificar

### Backend

| Archivo | Cambio |
|---------|--------|
| `backend/app/models.py` | `patient_id` nullable en `PatientIntakeLink`, agregar `link_type` |
| `backend/app/schemas.py` | Agregar `link_type` a `IntakeLinkCreate`, `IntakeLinkOut`, `IntakeLinkPublicMeta`. Limitar `IntakeUpdateSubmit` a solo los campos permitidos |
| `backend/app/api/intake_links.py` | Adaptar create_link para `link_type` y patient_id opcional. Adaptar public_submit para crear paciente si no existe. Limitar update a campos permitidos |
| `backend/alembic/versions/` | Migración: `patient_id` nullable, agregar `link_type` |

### Frontend

| Archivo | Cambio |
|---------|--------|
| `frontend/src/types/index.ts` | Agregar `link_type` a `IntakeLink`, `IntakePublicMeta` |
| `frontend/src/services/api.ts` | Adaptar `createIntakeLink` para enviar `link_type`. Agregar función `updateIntakeForm` |
| `frontend/src/pages/PublicIntake.tsx` | Detectar `link_type` y mostrar formulario completo (register) o simplificado (update). Usar PUT /update para update |
| `frontend/src/components/sharing/ShareModal.tsx` | Selector de tipo "Registro" / "Actualización" + selector de paciente para update. Eliminar WhatsApp directo |
| `frontend/src/pages/IntakeLinks.tsx` | Mostrar tipo de link (registro/actualización) en la lista |

---

## Verificación

1. **Registro**: Crear link de registro → abrir enlace → llenar formulario completo → enviar → paciente creado en el sistema
2. **Actualización**: Crear link de actualización para paciente existente → abrir enlace → ver formulario simplificado con datos pre-llenados → modificar peso → enviar → peso actualizado en DB
3. **Share**: En móvil, menú nativo del SO al tocar "Compartir". En desktop, Copiar enlace y Correo.
4. **Sin WhatsApp directo**: No hay botón de WhatsApp en ningún lado
5. **Expiración**: Link expira según días configurados
6. **Build**: `npx tsc --noEmit && npm run build` sin errores
