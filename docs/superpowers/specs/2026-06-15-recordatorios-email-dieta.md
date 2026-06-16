# Recordatorios Automáticos por Email — Seguimiento de Dietas

**Date:** 2026-06-15
**Status:** Design approved

## Contexto

Actualmente, después de que el doctor genera una dieta para un paciente, no hay seguimiento automático. El paciente no recibe recordatorios para actualizar sus métricas (peso, altura, etc.), lo que hace que los datos se vuelvan obsoletos.

Se necesita un sistema que, **30 días después de creada la dieta**, envíe automáticamente un email al paciente con un link de actualización para que ingrese sus nuevas medidas.

## Decisión de implementación

- **Gmail API** vía HTTP (no SMTP) para compatibilidad con Railway hobby
- **APScheduler** corriendo dentro del proceso FastAPI (sin dependencias externas)
- **Modelo DietReminder** para evitar duplicados de recordatorios
- **Email obligatorio** en el formulario de registro

## Componentes nuevos

### Backend

| Archivo | Propósito |
|---------|-----------|
| `backend/app/models.py` | Nuevo modelo `DietReminder` |
| `backend/app/services/email_service.py` | Envío de emails vía Gmail API HTTP |
| `backend/app/services/reminder_service.py` | Lógica del recordatorio: detectar dietas, crear links, enviar |
| `backend/app/tasks/scheduler.py` | APScheduler configurado en startup de FastAPI |
| `backend/app/templates/reminder_email.html` | Template HTML del email |

### Configuración (.env)

```
GMAIL_CLIENT_ID=xxx
GMAIL_CLIENT_SECRET=xxx
GMAIL_REFRESH_TOKEN=xxx
GMAIL_SENDER_EMAIL=doctora@gmail.com
```

### Frontend

| Archivo | Cambio |
|---------|--------|
| `PublicIntake.tsx` | Email obligatorio en registro (con `*`) |

## Flujo completo

```
Día 0:  Dieta generada → created_at = 2026-06-15
Día 30: Scheduler (cada 24h) detecta dieta con 30 días
        → Verifica que paciente tenga email
        → Verifica que no haya recordatorio previo (DietReminder)
        → Crea update link (7 días expiración)
        → Envía email vía Gmail API
        → Guarda DietReminder (evita duplicados)
Día 37: Link expira (si no se usó)
Día 60: Si la dieta sigue activa → otro recordatorio automático
```

## Verificación

1. Crear dieta para paciente con email → esperar simulación de 30 días → verificar que se crea link y se envía email
2. Verificar que no se envían recordatorios duplicados (DietReminder previene)
3. Email obligatorio en formulario de registro
4. Build backend + frontend sin errores
