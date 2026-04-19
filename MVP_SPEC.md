# Diet Telegram Agent MVP

## Objetivo

Construir un sistema donde la doctora administre pacientes desde un panel web y opere por Telegram con un agente que pueda consultar, actualizar y generar dietas usando datos reales del paciente.

## Alcance MVP

Incluye:
- Panel de administracion para la doctora
- Pacientes creados manualmente o por link
- Formulario publico para ficha del paciente
- Bot de Telegram solo para la doctora
- Generacion de dieta personalizada
- Historial de dietas y ficha clinica

No incluye en esta fase:
- Bot web
- Conversacion directa paciente-bot
- Multiples doctores por clinica con permisos complejos
- Analiticas avanzadas con graficas clinicas profundas
- Edicion colaborativa en tiempo real

## Stack Recomendado

- Backend: FastAPI + SQLAlchemy + Alembic + PostgreSQL + Redis + OpenAI
- Frontend admin: React + TypeScript + Vite + Tailwind + Zustand + React Query
- Canal conversacional: Telegram
- Base tecnica: `version_simplificada`
- Base de dominio nutricional: `AlexProyectPage`

## Arquitectura General

1. Panel de administracion
- Login de doctora
- Dashboard con metricas
- Modulo de pacientes
- Modulo de dietas
- Modulo de links de registro
- Configuracion de Telegram
- Historial de acciones

2. Formulario publico por link
- El paciente recibe un link unico
- Llena su ficha personal y clinica
- El sistema guarda o actualiza su perfil
- La doctora luego puede trabajar con ese paciente desde Telegram

3. Bot de Telegram para la doctora
- Consulta datos del paciente
- Modifica campos del paciente
- Resume historial
- Genera dieta
- Ajusta dieta existente
- Responde con lenguaje natural, pero operando sobre datos reales

4. Motor de IA
- Interpreta intencion
- Decide si consulta DB, actualiza DB o genera dieta
- Si faltan datos, pregunta
- Si la accion es critica, confirma antes de guardar

## Modelo de Datos MVP

Entidades minimas:
- `doctor`
- `patient`
- `patient_profile`
- `patient_metrics`
- `patient_intake_link`
- `diet`
- `diet_version`
- `telegram_doctor_binding`
- `conversation_state`
- `audit_log`

### doctor
- id
- user_id
- name
- email
- telegram_user_id
- is_active

### patient
- id
- doctor_id
- first_name
- last_name
- birth_date
- sex
- whatsapp
- email
- country
- city
- is_active
- source: `admin | intake_link | telegram`

### patient_profile
- patient_id
- objective
- diseases
- medications
- food_allergies
- foods_avoided
- medical_history
- dietary_style
- food_preferences
- disliked_foods
- meal_schedule
- water_intake
- activity_level
- stress_level
- sleep_quality
- budget_level
- adherence_level
- extra_notes

### patient_metrics
- patient_id
- weight
- height
- neck_size
- chest_size
- waist_size
- hip_size
- leg_size
- calf_size
- recorded_at

### patient_intake_link
- id
- doctor_id
- patient_id nullable
- token
- expires_at
- is_used
- max_uses
- use_count
- created_at

### diet
- id
- patient_id
- created_by_doctor_id
- status
- summary
- structured_plan_json
- notes
- created_at

### diet_version
- id
- diet_id
- version_number
- prompt_context_json
- output_json
- doctor_instruction
- created_at

### telegram_doctor_binding
- id
- doctor_id
- telegram_user_id
- created_at
- updated_at

### conversation_state
- id
- doctor_id
- telegram_user_id
- context_data
- updated_at

### audit_log
- id
- actor_type
- actor_id
- action
- entity_type
- entity_id
- payload_json
- created_at

## Formulario del Paciente

Se llenara por link o desde el panel por la doctora.

### 1. Datos personales
- Nombre
- Apellido
- Fecha de nacimiento
- Sexo
- WhatsApp
- Correo electronico
- Pais
- Ciudad

### 2. Medidas actuales
- Peso actual
- Altura
- Cuello
- Pecho
- Cintura
- Cadera
- Pierna
- Pantorrilla

### 3. Objetivo
- Cual es tu meta principal
- Opciones:
  - Bajar de peso
  - Mantenerme
  - Ganar masa muscular
  - Mejorar mi salud
  - Aumentar energia
  - Otro

### 4. Salud y antecedentes
- Tienes alguna enfermedad o diagnostico medico
- Tomas medicamentos actualmente
- Tienes lesiones o limitaciones fisicas
- Has tenido cambios recientes importantes en tu salud
- Historia clinica relevante

### 5. Alimentacion
- Hay alimentos que no consumes
- Tienes alergias o intolerancias
- Sigues algun estilo de alimentacion
- Opciones:
  - Ninguno
  - Vegetariana
  - Vegana
  - Baja en carbohidratos
  - Sin gluten
  - Otra
- Alimentos que te gustan
- Alimentos que no te gustan

### 6. Habitos diarios
- Cuantas comidas haces al dia
- A que hora desayunas normalmente
- A que hora almuerzas
- A que hora cenas
- Sueles picar entre comidas
- Cuanta agua tomas al dia

### 7. Actividad fisica
- Realizas ejercicio
- Frecuencia semanal
- Tipo de actividad
- Nivel de actividad:
  - Muy baja
  - Baja
  - Moderada
  - Alta
  - Muy alta

### 8. Sueno y estres
- Cuantas horas duermes
- Calidad del sueno:
  - Muy mala
  - Mala
  - Regular
  - Buena
  - Muy buena
- Nivel de estres:
  - 1 Muy bajo
  - 2 Bajo
  - 3 Moderado
  - 4 Alto
  - 5 Muy alto

### 9. Presupuesto
- Que presupuesto aproximado tienes para tu alimentacion
- Opciones:
  - Muy ajustado
  - Bajo
  - Medio
  - Medio alto
  - Flexible

### 10. Dificultades y adherencia
- Que es lo que mas te cuesta al seguir una dieta
- Opciones:
  - Ansiedad por comer
  - Falta de tiempo
  - Poco presupuesto
  - No me gusta cocinar
  - Como mucho fuera de casa
  - Antojos dulces
  - Antojos salados
  - Otro
- Que tan comprometido te sientes para seguir un plan
  - 1 Muy poco
  - 2 Poco
  - 3 Medio
  - 4 Alto
  - 5 Muy alto

### 11. Observaciones finales
- Hay algo mas que tu doctora deba saber para preparar tu plan

## Panel de Administracion MVP

Pantallas:
- Login
- Dashboard
- Pacientes
- Detalle de paciente
- Nuevo paciente
- Links de registro
- Dietas
- Detalle de dieta
- Telegram

Funciones MVP:
- Crear paciente manualmente
- Editar ficha del paciente
- Registrar medidas
- Generar link de llenado
- Ver si el paciente completo el link
- Generar dieta
- Ver historial de dietas
- Exportar o visualizar dieta

Dashboard MVP:
- Total de pacientes
- Pacientes nuevos
- Pacientes con ficha incompleta
- Dietas generadas
- Ultimas acciones

## Telegram de la Doctora

Intents MVP:
- `buscar_paciente`
- `ver_ficha_paciente`
- `ver_historial_paciente`
- `actualizar_dato_paciente`
- `registrar_medida`
- `generar_dieta`
- `ajustar_dieta`
- `ver_ultima_dieta`
- `enviar_link_registro`
- `resumen_dashboard`

Ejemplos:
- `muestrame la ficha de Ana Perez`
- `actualiza el peso de Ana a 168 libras`
- `que alergias tiene Luis`
- `enviale el link de registro a Carmen`
- `hazle una dieta a Pedro`
- `ajusta la dieta de Laura sin lacteos`

Estados conversacionales MVP:
- `idle`
- `awaiting_patient_selection`
- `awaiting_field_value`
- `awaiting_metric_value`
- `awaiting_diet_confirmation`
- `awaiting_missing_profile_data`
- `awaiting_link_target_confirmation`

## Reglas del Agente

- Nunca inventar datos del paciente
- Si faltan datos clave para dieta, preguntar antes de generar
- Confirmar cambios sensibles antes de guardar
- Responder en lenguaje natural
- Guardar cambios en base de datos y registrar auditoria

Datos minimos para generar dieta:
- Edad o fecha de nacimiento
- Sexo
- Peso
- Altura
- Objetivo
- Enfermedades o restricciones relevantes
- Alergias o alimentos no consumidos
- Pais y ciudad

## Formato de Dieta

Principalmente JSON estructurado para el sistema, con resumen en texto para Telegram.

```json
{
  "patient_id": 12,
  "summary": "Plan enfocado en perdida de peso con alimentos accesibles.",
  "daily_calories": 1800,
  "macros": {
    "protein_pct": 30,
    "carbs_pct": 40,
    "fat_pct": 30
  },
  "days": [
    {
      "day": 1,
      "breakfast": "....",
      "lunch": "....",
      "snack": "....",
      "dinner": "...."
    }
  ]
}
```

## Fases de Implementacion

### Fase 1
- Base del proyecto con stack de `version_simplificada`
- Modelos de doctor, paciente, perfil y metricas
- Panel admin de pacientes
- Links de registro

### Fase 2
- Bot Telegram para doctora
- Lectura y actualizacion de ficha
- Binding de doctora con Telegram

### Fase 3
- Generacion de dieta
- Historial de dietas
- Resumen por Telegram
- Exportacion PDF

## Decision Tecnica

- Usar `version_simplificada` como base completa
- Migrar el dominio de nutricion desde `AlexProyectPage`
- Reemplazar intents de citas por intents clinico-nutricionales
- Mantener Telegram como unico canal conversacional del MVP
