# Project Status

## Portfolio / production hardening (2026-04)

- Root [README.md](./README.md), [LICENSE](./LICENSE), and CI checks (Ruff, TypeScript, ESLint).
- Auth: frontend clears React session when API returns `401` (aligned with `localStorage`).
- Single-doctor model: `POST /api/auth/register` returns `403` if a doctor already exists; `GET /api/auth/registration-open` for the login UI.
- Telegram: `TELEGRAM_WEBHOOK_SECRET` required in production; webhook idempotency via `update_id`; internal errors logged and acknowledged with `200` + `{ "ok": true }` to limit retry storms.
- Ops: `GET /api/health/ready` checks the database; SQLAlchemy engine uses `pool_pre_ping`.

## Proyecto

Nombre de trabajo: `diet_telegram_agent`

Descripcion:
Sistema para que una doctora administre pacientes desde un panel web y opere por Telegram con un agente de IA capaz de consultar, actualizar y generar dietas personalizadas usando la informacion real del paciente.

## Base de Referencia

- Base tecnica: `version_simplificada`
- Base de dominio nutricional: `AlexProyectPage`

## Estado Actual

Estado general: `Fase 1 de diseno tecnico completada`

## Log de Progreso

### Fase 0 - Analisis inicial
Estado: `Completada`

Logrado:
- Se analizaron los dos proyectos existentes del directorio
- Se identifico `version_simplificada` como la mejor base tecnica
- Se identifico `AlexProyectPage` como fuente del dominio de pacientes y dietas
- Se definio que el canal conversacional del MVP sera Telegram
- Se definio que el sistema tendra panel admin, links de registro y agente para la doctora
- Se definio el formulario inicial del paciente
- Se creo el documento de especificacion MVP

Pendiente para la siguiente fase:
- Definir tablas y endpoints exactos
- Definir estructura de carpetas del nuevo proyecto
- Iniciar el esqueleto tecnico del proyecto

### Fase 1 - Diseno tecnico base
Estado: `Completada`

Logrado:
- Se definieron las tablas base del sistema
- Se definieron relaciones entre doctora, paciente, perfil, metricas, links y dietas
- Se definieron los endpoints iniciales del panel admin
- Se definieron los endpoints del formulario publico por link
- Se definio la estructura minima de carpetas del nuevo proyecto
- Se creo el documento tecnico `PHASE_1_SCHEMA_API.md`

Pendiente para la siguiente fase:
- Crear el esqueleto real del backend y frontend
- Implementar modelos y migraciones iniciales
- Implementar CRUD de pacientes y links de registro

## Fases Planeadas

### Fase 1 - Fundacion del proyecto
Objetivo:
- Crear la base tecnica del nuevo sistema
- Definir modelos principales
- Preparar panel admin inicial

Estado: `Completada`

Logrado:
- Se creo la estructura real de `backend` y `frontend`
- Se agrego FastAPI base con router y endpoints placeholder
- Se definieron modelos SQLAlchemy en `backend/app/models.py`
- Se agregaron schemas base en `backend/app/schemas.py`
- Se creo el esqueleto de frontend con rutas y paginas base

Pendiente para la siguiente fase:
- Implementar CRUD real de pacientes y perfiles
- Implementar generacion y validacion de links de intake
- Conectar frontend con API real

### Fase 2 - Pacientes y links
Objetivo:
- CRUD de pacientes
- Formulario publico por link
- Registro de ficha clinica y nutricional

Estado: `Pendiente`

### Fase 3 - Telegram de la doctora
Objetivo:
- Consultar ficha del paciente
- Actualizar datos del paciente
- Ver historial resumido

Estado: `Pendiente`

### Fase 4 - Generacion de dieta
Objetivo:
- Generar dieta personalizada
- Guardar historial de versiones
- Entregar resumen por Telegram

Estado: `Pendiente`

### Fase 5 - Cierre MVP
Objetivo:
- Exportacion
- Validaciones finales
- Pruebas del flujo completo

Estado: `Pendiente`

## Regla de Actualizacion

Este documento debe actualizarse al cerrar cada fase con:
- Estado
- Logrado
- Pendientes
- Riesgos detectados
- Proximo paso
