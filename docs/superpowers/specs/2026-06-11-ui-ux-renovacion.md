# UI/UX Renovación — Dra. Acosta Nutribot

**Fecha:** 2026-06-11
**Estilo:** Dashboard SaaS Profesional (Enfoque B)
**Dependencias nuevas:** `framer-motion`, `@phosphor-icons/react`

---

## Objetivo

Transformar la interfaz de un diseño básico Tailwind a un dashboard profesional moderno tipo Linear/Vercel, manteniendo la funcionalidad existente. Todo cambio debe hablar el lenguaje del médico: **cero IDs numéricos visibles, cero jerga técnica, todo en lenguaje natural.**

---

## Principios de Diseño

1. **Lenguaje de médico, no de programador** — "Dieta activa hace 3 días", no `status: generated #42`
2. **Profesional sin ser frío** — Slate neutro + Emerald como único acento, fondo `#f9fafb`
3. **Visible y accesible** — Las acciones importantes (crear dieta, enviar formulario) deben estar a un click desde múltiples lugares
4. **Preparado para escalar** — Estructura lista para batch de dietas futuro, componentes reciben arrays
5. **Responsive** — Misma experiencia en desktop, tablet, y PWA mobile

---

## Sistema de Diseño

### Color
| Token | Valor | Uso |
|-------|-------|-----|
| Fondo | `#f9fafb` (slate-50) | Página |
| Superficie | `#ffffff` | Cards, sidebar, modales |
| Texto principal | `slate-800` | Headings |
| Texto secundario | `slate-500/slate-600` | Labels, metadata |
| Acento | `emerald-600` (#059669) | Botones primarios, links, activos |
| Acento hover | `emerald-700` | Hover states |
| Error | `red-500/red-600` | Validación, estados negativos |
| Éxito | `emerald-500` | Confirmaciones |
| Borde | `slate-200/50` | Separadores sutiles |

### Tipografía
- Sistema nativo (`system-ui, -apple-system, sans-serif`) — sin dependencias de fuentes externas
- Headings: `tracking-tight`, `font-semibold`
- Números/métricas: `font-mono`, `tracking-tight`, `tabular-nums`
- Cuerpo: `text-base`, `leading-relaxed`, `max-w-[65ch]` en bloques de texto

### Sombras
- Cards: `shadow-[0_20px_40px_-15px_rgba(0,0,0,0.05)]` (difusión suave)
- Sidebar: sin sombra, separado por borde derecho `border-r border-slate-200`
- Modales/drawers: `shadow-xl` con overlay blur

### Bordes
- Cards: `rounded-2xl`
- Botones: `rounded-full` (pills) o `rounded-xl`
- Inputs: `rounded-xl`
- Avatares: `rounded-full`

### Iconos
- `@phosphor-icons/react` — StrokeWidth 1.5 (light)
- Nunca emojis en la UI

### Animaciones
- `framer-motion` para: transiciones de página, drawer slide-in, fade-in staggered de listas
- Curva: `cubic-bezier(0.16, 1, 0.3, 1)` para transiciones CSS
- Hover: `scale-[0.98]` en botones (tactile feedback)
- Nunca animar `top`, `left`, `width`, `height` — solo `transform` y `opacity`

---

## 1. Layout Principal

### Sidebar
- **Desktop:** Fijo izquierdo, `w-60`, `bg-white`, `border-r border-slate-200`
- Items: icono Phosphor + label, estado activo con indicador lateral `emerald-600` y fondo `emerald-50/50`
- Navegación: Dashboard, Pacientes, Dietas, Formularios, Admin (si admin)
- Footer: avatar doctor + nombre + email + botón "Cerrar sesión"
- **Mobile:** Drawer overlay con `backdrop-blur-sm`, hamburger animado → X

### Top Bar
- Breadcrumbs tipo Linear: `Dashboard / Pacientes / María García`
- Derecha: avatar circular del doctor con menú desplegable (Perfil, Cerrar sesión)
- **Mobile:** Header sticky con hamburger + título de página actual

### Contenido
- `max-w-[1400px] mx-auto`, `px-4 md:px-8`, `py-6`
- Breadcrumbs presentes en todas las páginas anidadas

---

## 2. Dashboard

### KPIs (fila superior)
4 tarjetas en bento grid responsivo:
- **Total pacientes:** Número grande, tendencia vs mes anterior (↑↓)
- **Nuevos este mes:** Conteo de últimos 30 días
- **Perfiles incompletos:** Con link "Ver todos →"
- **Dietas generadas:** Total acumulado

Cada tarjeta: `bg-white`, `rounded-2xl`, `p-6`, shadow difusa, número en `font-mono text-4xl tracking-tight`

### Actividad Reciente (columna izquierda, 2/3)
Timeline de últimas 10 acciones:
- Avatar circular con iniciales + descripción legible + timestamp relativo ("hace 3 horas")
- Scrollable, max-height controlado
- Link "Ver toda la actividad →"

### Perfiles Completados (columna derecha, 1/3)
- Barra de progreso horizontal: `193 de 247 completados (78%)`
- Breakdown: 🟢 Completo / 🟡 Parcial / 🔴 Vacío
- Subtítulo: "X pacientes necesitan enviar formulario"

### Animación
- KPIs entran con fade-up staggered al montar (Framer `staggerChildren: 0.1`)

---

## 3. Lista de Pacientes

### Layout
- Sin IDs visibles en ningún lugar
- Cada fila: avatar con iniciales (círculo, color único derivado del nombre), nombre completo, última consulta (texto legible), estado (badge: Activo, Pendiente, Nuevo), acciones (menú contextual `···`)
- Búsqueda predictiva: input con `usePatientSearch` existente, muestra resultados mientras escribes
- Filtros con labels humanos: "Todos", "Con dieta activa", "Perfil pendiente", "Nuevos este mes"
- Paginación con números de página

### Estados
- Loading: skeleton rows (4-5 barras grises animadas con shimmer)
- Empty: ilustración sutil + "Aún no hay pacientes" + botón "Crear primer paciente"
- Error: mensaje inline con botón de reintentar

### Crear paciente
- Botón **"+ Nuevo Paciente"** prominente (top-right)
- Abre drawer lateral derecho (`framer-motion` slide-in)
- Drawer contiene formulario completo (ver sección 4)
- Al guardar: drawer cierra, lista se actualiza, toast de confirmación

### Menú contextual (···)
- Ver perfil
- Nueva dieta
- Enviar formulario
- Editar datos

---

## 4. Crear Paciente (Drawer)

### Drawer lateral derecho
- Título: "Nuevo Paciente" + botón cerrar (✕)
- Ancho: `w-full md:w-[480px]`, `max-w-full`
- Overlay: `bg-black/20 backdrop-blur-sm`

### Secciones del formulario

**Datos Personales (siempre visible):**
- Nombre *, Apellido * (obligatorios, marcados)
- Fecha de nacimiento (date picker nativo)
- Sexo (select: Femenino, Masculino, No especificar)
- País, Ciudad
- WhatsApp, Email

**Perfil Clínico (colapsable, opcional):**
- Objetivo (select: Pérdida de grasa, Ganancia muscular, Mantenimiento, etc.)
- Enfermedades (textarea)
- Medicamentos (textarea)
- Alergias alimentarias (textarea)
- Alimentos a evitar (textarea)
- Historial médico (textarea)
- Estilo de alimentación (select)
- Preferencias alimentarias (textarea)
- Comidas que no le gustan (textarea)

**Métricas Iniciales (colapsable, opcional):**
- Peso (kg)
- Altura (cm)
- Resto de medidas (cuello, pecho, cintura, cadera, pierna, pantorrilla) — colapsado por defecto

### Comportamiento
- Validación inline: campos requeridos muestran error debajo
- Guardar llama a `createPatient` + `PUT /profile` + `POST /metrics` secuencialmente
- Éxito: toast verde "Paciente creado", drawer cierra, lista refresca
- Error: toast rojo con mensaje, drawer permanece abierto
- Estados: loading en botón mientras guarda, deshabilitado para evitar doble click

---

## 5. Perfil del Paciente

### Layout
- Vista única scrollable con secciones — **sin tabs**
- Breadcrumb: `Pacientes / María García`
- Botones de acción visibles en la parte superior: "Editar Datos", "Nueva Dieta", "Enviar Formulario", "Registrar Métricas"

### Secciones

**Cabecera:**
- Avatar grande con iniciales
- Nombre completo, edad, sexo, ciudad
- Email, WhatsApp (si disponibles)

**Resumen:**
- Peso actual, altura, IMC con clasificación (Normal, Sobrepeso, etc.)
- Último registro: "hace 2 semanas" con link a registrar nuevo
- Dieta activa: tipo de plan, calorías, fecha de generación — con botón "Ver dieta completa →"

**Datos Clínicos:**
- Grid de 2 columnas con etiquetas legibles
- Objetivo, enfermedades, medicamentos, alergias, alimentos evitados, estilo de alimentación

**Historial de Métricas:**
- Mini sparkline de peso (gráfico simple SVG o div con alturas relativas)
- Tabla: Fecha, Peso, Altura, IMC — últimas 10 entradas
- Botón "+ Registrar Métricas" → abre modal pequeño con peso + altura + medidas opcionales

**Dietas Anteriores:**
- Lista de tarjetas pequeñas: tipo de plan, calorías, fecha → link a detalle
- Botón "+ Nueva Dieta" pre-selecciona este paciente

### Edición de datos
- Botón "Editar Datos" convierte las secciones en formularios inline editables
- Modo "Guardar Cambios" / "Cancelar"

---

## 6. Dietas

### Lista de Dietas
- **Sin IDs** — columnas: Paciente (avatar + nombre), Plan (tipo + calorías), Estado (badge legible), Generada (fecha relativa)
- Búsqueda por nombre de paciente (usa `usePatientSearch`)
- Filtros: Todas, Activas, Pendientes, Descartadas
- Paginación

### Estados de dieta (badges legibles):
| Estado backend | Badge UI |
|----------------|----------|
| `generated` | ✅ Activa |
| `pending_approval` | ⏳ Pendiente de aprobación |
| `draft` | 📝 Borrador |
| `discarded` | 🗑️ Descartada |
| `queued` | ⏱️ En cola |
| `generating` | 🔄 Generando... |

### Nueva Dieta (Individual) — Wizard simplificado

**Acceso desde:**
- Barra superior: "+ Nueva Dieta"
- Perfil del paciente: "Nueva Dieta" (pre-selecciona paciente)
- Lista de dietas: "+ Nueva Dieta"

**Pasos del wizard:**
1. **Paciente** — Búsqueda por nombre con resultados mostrando avatar, ciudad, estado del perfil. Si el perfil está incompleto, muestra advertencia y bloquea continuación (ofrece enviar formulario).
2. **Nota** (opcional) — Instrucción del doctor en textarea
3. **Plan** — Duración (presets 7/14/28/42/56/84 días), comidas por día (2-5), modo (Auto/Manual). Auto recomendado.
4. **Revisar** — Resumen de selecciones + botón "Generar Dieta"
5. **Preview** — DietPreviewPanel existente con acciones (Aprobar, Descartar, Descargar PDF)

### Preparación para batch futuro
- Componentes internos del wizard aceptan array de pacientes (`patientIds: number[]`)
- Status `queued` y `generating` ya visibles en la UI
- Botón "Generar en Lote" oculto con feature flag `NEXT_FEATURES.batchDiets`
- Checkboxes en lista de pacientes listos para recibir selección múltiple

---

## 7. Compartir / Formularios de Ingesta

### Acceso desde múltiples puntos
- Lista de pacientes: menú contextual (···) → "Enviar formulario"
- Perfil del paciente: botón visible "Enviar formulario"
- Página `/formularios` (renombrada de `/intake-links`): gestión completa

### Modal de compartir
Al hacer click en "Enviar formulario":

1. **Seleccionar expiración:** dropdown (1, 3, 7, 14, 30 días — default 7)
2. **Link generado:** `https://nutribot.app/formulario/aB3xK9mW`
3. **Botón Copiar:** con feedback "¡Copiado!" temporal
4. **Botón WhatsApp:** abre `wa.me` con mensaje pre-compuesto en español
5. **Botón Email:** abre `mailto:` con asunto y cuerpo pre-compuestos
6. **Explicación:** texto pequeño explicando qué podrá hacer el paciente

### Página de Formularios (renombrada)
- URL: `/formularios` (redirect de `/intake-links` para no romper nada)
- Lista de links creados: paciente, estado (Activo, Usado, Revocado, Expirado), creado, expira, acciones (Copiar link, Revocar)
- Botón "+ Nuevo formulario" → abre modal de compartir

### Terminología
- "Formulario de ingesta" o "Formulario del paciente" — nunca "Intake link"
- "Enviar formulario" — nunca "Create intake link"

---

## 8. Estados Globales

Todas las páginas deben implementar:

### Loading
- Skeleton loaders que imitan el layout real
- Shimmer animation sutil (CSS `animate-pulse` o Framer)
- No spinners circulares genéricos

### Empty
- Ilustración/icono sutil + texto descriptivo
- Botón de acción primaria (ej: "Crear primer paciente")
- Sin estados vacíos huérfanos

### Error
- Mensaje inline con descripción del error
- Botón "Reintentar" que vuelve a ejecutar la query
- No alerts nativos del navegador

### Toasts
- Confirmaciones breves: "Paciente creado", "Dieta generada", "Link copiado"
- Errores: toast rojo con mensaje descriptivo
- Posición: bottom-right en desktop, top-center en mobile

---

## 9. PWA

- Todos los cambios se reflejan en la PWA automáticamente
- `theme_color`: `#059669` (emerald-600)
- `background_color`: `#f9fafb`
- Navegación adaptada a mobile: sidebar drawer, top bar sticky
- Formularios usan inputs nativos (date, select) para mejor experiencia en mobile
- Touch targets mínimos 44px (WCAG)

---

## 10. Plan de Implementación (Alto Nivel)

### Fase 1: Fundación
- Instalar `framer-motion`, `@phosphor-icons/react`
- Rediseñar `AdminLayout` (sidebar + top bar + breadcrumbs)
- Crear componentes base: Skeleton, Toast, EmptyState, Badge, Avatar

### Fase 2: Dashboard
- Rediseñar `Dashboard.tsx` — bento grid, KPIs, timeline, progreso

### Fase 3: Pacientes
- Rediseñar `Patients.tsx` — avatares, estados legibles, búsqueda predictiva, menú contextual
- Crear drawer de "Nuevo Paciente" con formulario completo
- Rediseñar `PatientDetail.tsx` — vista única scrollable sin tabs

### Fase 4: Dietas
- Rediseñar `Diets.tsx` — sin IDs, badges legibles, búsqueda por nombre
- Mejorar `DietWizard.tsx` — búsqueda por nombre en paso 1, bloqueo por perfil incompleto
- Agregar feature flag para batch futuro

### Fase 5: Compartir
- Rediseñar modal de compartir
- Renombrar `/intake-links` → `/formularios` (con redirect)
- Integrar acceso desde lista de pacientes y perfil

### Fase 6: Pulido
- Revisar todos los estados (loading, empty, error) en cada página
- Verificar responsive (mobile, tablet, desktop)
- Probar PWA en dispositivo real
- Limpiar estilos inline restantes (Dashboard, Login)

---

## Verificación

- [ ] Navegar dashboard — ver KPIs, actividad, progreso — sin IDs
- [ ] Crear paciente completo desde drawer — verificar en lista
- [ ] Abrir perfil de paciente — ver resumen, datos clínicos, sparkline, dietas — sin tabs
- [ ] Crear dieta individual desde perfil y desde barra superior
- [ ] Ver lista de dietas — sin IDs, badges en español
- [ ] Enviar formulario desde lista de pacientes y desde perfil
- [ ] Compartir por WhatsApp y Email
- [ ] Probar PWA en móvil — sidebar drawer, navegación, formularios
- [ ] Verificar estados vacíos y de error en cada página
- [ ] Verificar responsive en 375px, 768px, 1440px
