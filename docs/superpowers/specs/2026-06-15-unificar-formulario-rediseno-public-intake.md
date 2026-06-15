# Unificar Creación de Formularios + Rediseño PublicIntake + Fix Responsive

**Date:** 2026-06-15
**Status:** Design approved

## Cambio 1: Unificar en un solo botón con dropdown

**Actual:** Dos botones separados ("Nuevo Formulario" + "Registro Rápido") que confunden al usuario.

**Propuesto:** Un solo botón "Nuevo Formulario" en la cabecera de IntakeLinks. Al hacer clic, se abre un dropdown con dos opciones:

| Opción | Descripción | Flujo |
|--------|-------------|-------|
| 📝 **Registro** | Para paciente nuevo — se crea automáticamente al enviar | Abre ShareModal directamente con `link_type="register"` |
| 🔄 **Actualización** | Para paciente existente — elige quién actualiza datos | Muestra selector de paciente, luego ShareModal con `link_type="update"` |

**Eliminar:**
- El botón independiente "Registro Rápido"
- El paso de selector de paciente del flujo actual de "Nuevo Formulario" (ahora va dentro del dropdown)

## Cambio 2: Rediseño completo de PublicIntake

### Estado actual
- 100% inline CSS (`CSSProperties`) — sin Tailwind
- Labels en inglés
- Sin indicación de campos obligatorios
- Sin formato de tarjeta (card)
- Inputs cuadrados sin bordes redondeados
- No se ve bien en móvil

### Estado propuesto
- **Migrar de inline styles a Tailwind CSS** — consistente con el resto de la app
- **Todo en español** — labels, placeholders, mensajes, títulos
- **Campos obligatorios con asterisco rojo** (`*`) — los opcionales sin asterisco
- **Layout de tarjeta (card)** con `rounded-2xl`, `shadow-sm`, `border-slate-100`
- **Secciones con cabeceras verdes** (mismo estilo que PatientDetail)
- **Mobile-first** — grid responsive en nombre/apellido, peso/altura
- **Hint de privacidad** al final

### Campos obligatorios vs opcionales (registro)

**Obligatorios** (con `*`):
- Nombre, Apellido, Fecha de nacimiento, Sexo, País, Ciudad
- Peso, Altura
- Objetivo principal
- Alergias alimentarias
- Alimentos a evitar

**Opcionales** (sin `*`):
- Email, WhatsApp
- Enfermedades, Medicamentos, Historial médico
- Estilo de alimentación, Preferencias, Alimentos que no le gustan
- Todos los hábitos (agua, estrés, sueño, etc.)
- Medidas corporales extra (cuello, pecho, cintura, etc.)

### Formulario de actualización
Mantiene el formato de card, con solo estos campos (todos opcionales):
- Nombre, Apellido, Email, WhatsApp, País, Ciudad
- Peso, Altura

### Títulos y secciones

```
Registro de Paciente                    ← h1 grande
Completa tus datos para tu plan...     ← subtítulo

── Datos personales ──                  ← sección (verde)
Nombre * | Apellido *                  ← grid 2 columnas
Fecha de nacimiento * | Sexo *
Email | WhatsApp
País * | Ciudad *

── Medidas corporales ──
Peso * | Altura *

── Salud y objetivo ──
Objetivo principal *
Alergias alimentarias *
Alimentos a evitar *
Enfermedades | Medicamentos | Historial...

── Hábitos ──
Agua | Actividad | Estrés | Sueño...

[Enviar registro]                       ← botón verde
```

## Cambio 3: Fix responsive

| Problema | Solución |
|----------|----------|
| HeightInput ft/in desborda en móvil | Stack vertical (`flex-col`) en móvil, horizontal en desktop |
| Tablas sin scroll horizontal | Agregar `overflow-x-auto` a tablas en Patients, Diets, PatientDetail |
| Formularios sin padding en móvil | Asegurar `px-4` en contenedores |
| WeightInput/HeightInput se montan | Cambiar `flex` gap a `flex-wrap` o `flex-col` en mobile |

## Archivos a modificar

| Archivo | Cambios |
|---------|---------|
| `frontend/src/pages/IntakeLinks.tsx` | Unificar botones en dropdown, eliminar flujo "crear y seleccionar paciente" separado |
| `frontend/src/pages/PublicIntake.tsx` | Rediseño completo: Tailwind, español, cards, required indicators, mobile responsive |
| `frontend/src/components/ui/HeightInput.tsx` | Fix responsive: ft/in mode se apila verticalmente en móvil |
| `frontend/src/components/ui/WeightInput.tsx` | Fix responsive: wrap en móvil |

## Verificación

1. Un solo botón "Nuevo Formulario" con dos opciones en dropdown
2. Formulario de registro en español, con estilo de card, asteriscos en obligatorios
3. Formulario de actualización: solo los campos permitidos
4. HeightInput ft/in no se desborda en móvil
5. `npx tsc --noEmit && npm run build` sin errores
