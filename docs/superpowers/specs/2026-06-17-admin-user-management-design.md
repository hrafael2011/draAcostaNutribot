# Admin User Management — Design Spec

**Fecha:** 2026-06-17
**Proyecto:** Diet Agent (Dra. Acosta Nutribot)
**Estado:** Draft

---

## 1. Resumen

Sistema de administración de usuarios con portales independientes para admins y doctores, flujo de cambio de contraseña forzoso (primera vez y reseteo por admin), y recuperación de contraseña vía email con token de un solo uso.

---

## 2. Decisiones de Diseño

| Decisión | Opción Elegida |
|---|---|
| Portal admin | Independiente: `/admin` solo para admins, `/login` solo para doctores. Cada portal valida el rol al autenticar. |
| Creación de usuarios | Admin crea doctores y admins. Contraseña generada automáticamente por el sistema, mostrada en pantalla. Opcionalmente enviada por email. |
| Recuperación de contraseña | Disponible para ambos roles (admin y doctor). Vía email con token one-time de 30 minutos. |
| Pantalla de reseteo | Link con token → nueva contraseña + confirmar (sin email adicional) |
| Enfoque arquitectónico | Extender lo existente. No refactorizar modelo Doctor. |
| Branding | Reutilizar diseño actual "Dra. Acosta Nutribot" (emerald-600, logo, componentes UI existentes, template de email de recordatorios) |

---

## 3. Base de Datos

### 3.1. Tabla existente: `doctors` (sin cambios)

| Columna | Tipo | Notas |
|---|---|---|
| id | INTEGER PK | autoincrement |
| full_name | VARCHAR(160) | NOT NULL |
| email | VARCHAR(190) | UNIQUE, INDEX |
| phone | VARCHAR(30) | nullable |
| hashed_password | VARCHAR(255) | NOT NULL |
| role | VARCHAR(20) | DEFAULT 'doctor' |
| must_change_password | BOOLEAN | DEFAULT false |
| is_active | BOOLEAN | DEFAULT true |
| created_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | |

### 3.2. Tabla nueva: `password_reset_tokens`

| Columna | Tipo | Notas |
|---|---|---|
| id | INTEGER PK | autoincrement |
| doctor_id | INTEGER FK → doctors.id | NOT NULL, INDEX |
| token | VARCHAR(64) | UNIQUE, NOT NULL |
| expires_at | TIMESTAMPTZ | NOT NULL |
| used | BOOLEAN | DEFAULT false |
| created_at | TIMESTAMPTZ | DEFAULT now() |

**Relación:** 1 doctor → N tokens (uno por cada solicitud de reseteo).

**Índices:**
- UNIQUE(token)
- INDEX(doctor_id)
- INDEX(expires_at)

---

## 4. API Endpoints

### 4.1. Modificado

#### POST /api/auth/token

Se agrega parámetro `portal` (admin|doctor) al form-urlencoded body.

- `portal=admin`: valida que `doctor.role == "admin"`. Si no → 403.
- `portal=doctor`: valida que `doctor.role == "doctor"`. Si no → 403.
- Response no cambia: `{access_token, token_type, role, must_change_password}`

### 4.2. Nuevos

#### POST /api/auth/forgot-password

- **Auth:** No
- **Body:** `{email: string}`
- **Lógica:**
  1. Buscar doctor por email (cualquier rol). Si no existe, responder igual para no revelar información.
  2. Generar token: `secrets.token_urlsafe(32)` → 43 caracteres.
  3. Guardar en `password_reset_tokens` con `expires_at = now + 30min`.
  4. Enviar email con link: `APP_URL/reset-password?token={token}`.
- **Response (siempre el mismo):** `{ok: true, message: "Si el correo existe, recibirás instrucciones"}`

#### GET /api/auth/verify-reset-token

- **Auth:** No
- **Query:** `?token=xxx`
- **Lógica:**
  1. Buscar token en BD.
  2. Verificar no expirado (`expires_at > now`).
  3. Verificar no usado (`used = false`).
- **Response OK:** `{valid: true, email: "..."}`
- **Response FAIL:** `{valid: false}` (sin diferenciar causa)

#### POST /api/auth/reset-password

- **Auth:** No
- **Body:** `{token: string, new_password: string}`
- **Lógica:**
  1. Validar token (existe, no expirado, no usado).
  2. Hashear nueva contraseña con bcrypt.
  3. Actualizar `doctors.hashed_password`.
  4. Establecer `doctors.must_change_password = false`.
  5. Marcar `password_reset_tokens.used = true`.
- **Response OK:** `{ok: true}`
- **Response FAIL:** `{detail: "Token inválido o expirado"}`

### 4.3. Endpoints modificados

#### POST /api/admin/doctors — crear usuario (admin)

Se modifica para que el sistema genere la contraseña automáticamente. El admin ya no provee una contraseña.

- **Request:** `{full_name: string, email: string, role: "doctor"|"admin"}`
- **Lógica:** Generar contraseña con `secrets.token_urlsafe(12)`. Hashear con bcrypt. Guardar con `must_change_password=true`.
- **Response:** `{id, full_name, email, role, generated_password: "aB3x-Km9p"}`

#### POST /api/admin/doctors/{id}/reset-password — resetear contraseña (admin)

- **Lógica:** Generar nueva contraseña automática. Hashear. Establecer `must_change_password=true`.
- **Response:** `{generated_password: "zY9q-Wm4X"}`

### 4.4. Endpoints existentes que no cambian

- `POST /api/auth/change-password` — cambio forzoso
- `GET /api/admin/doctors` — listar usuarios (admin)
- `PATCH /api/admin/doctors/{id}` — editar usuario (admin)
- `GET /api/doctors/me` — perfil propio
- `PATCH /api/doctors/me` — actualizar perfil

---

## 5. Frontend

### 5.1. Árbol de rutas

```
/admin           → AdminLogin.tsx (sin auth, portal independiente)
/reset-password  → ResetPassword.tsx (sin auth, ?token=xxx)
/login           → Login.tsx (modificado: + forgot password link)
/change-password → ChangePassword.tsx (con auth)
/ → RequireAuth → AdminLayout
  /dashboard     → Dashboard
  /patients/*    → Patients...
  /diets/*       → Diets...
  /admin/users   → AdminUsers.tsx (requiere role=admin)
```

### 5.2. AdminLogin.tsx (/admin)

- **Diseño:** Mismo layout visual que Login.tsx (logo Dra. Acosta, tarjeta max-w-sm centrada).
- **Formulario:** Email + Password + Botón "Iniciar Sesión".
- **Link:** "¿Olvidaste tu contraseña?" → modal inline con input email.
- **API:** POST /api/auth/token con `portal=admin`.
- **Validación de rol:** Si el doctor no es admin → 403 "Acceso solo para administradores".
- **Redirección post-login:** `/admin/users`.
- **Estados:** IDLE, LOADING, ERROR_403, ERROR_401, MUST_CHANGE_PASSWORD, SUCCESS.

### 5.3. Login.tsx (/login — modificado)

- Se agrega `portal=doctor` a la llamada POST /api/auth/token.
- Se agrega link "¿Olvidaste tu contraseña?" debajo del botón de login.
- **Modal "Olvidé contraseña":** Input email + botón "Enviar enlace". Estados: IDLE → LOADING → SUCCESS (respuesta genérica). Sin revelar si el email existe o no.
- Si 403 por rol → mostrar "Acceso solo para doctores".

### 5.4. ResetPassword.tsx (/reset-password?token=xxx)

- **Fase 1 — VERIFYING:** Al montar el componente, llama a GET /api/auth/verify-reset-token. Muestra spinner "Verificando enlace...".
- **Fase 2 — INVALID_TOKEN:** Muestra "Este enlace ha expirado o no es válido. Solicita uno nuevo." + botón "Ir a iniciar sesión".
- **Fase 3 — VALID_TOKEN (formulario):**
  - Muestra email del usuario (solo para referencia).
  - Input: Nueva contraseña (mín. 8 caracteres, 1 mayúscula, 1 número).
  - Input: Confirmar contraseña.
  - Validación en vivo: botón habilitado solo si password valida y coincide.
  - Botón "Cambiar Contraseña" → POST /api/auth/reset-password.
  - Éxito: "Contraseña cambiada. Redirigiendo..." → redirect a /login tras 3s.
  - Error: "El enlace podría haber expirado."
- **Diseño:** Logo Dra. Acosta, tarjeta blanca, inputs con `focus:ring-emerald-500`.

### 5.5. AdminUsers.tsx (/admin/users)

Ya existe parcialmente. Se mejora con:

- **Tabla de usuarios:** Nombre, Email, Rol (badge), Estado (Activo/Inactivo), Creado, Acciones.
- **Estados:** LOADING (skeleton rows), EMPTY (empty state con CTA), LIST (con paginación si >20), ERROR_LOAD.
- **Modal "Crear Usuario":**
  - Campos: Nombre, Email, Rol (doctor/admin).
  - Contraseña auto-generada mostrada en pantalla con botones "Copiar" y "Regenerar".
  - Checkbox "Enviar contraseña por email al usuario".
  - Al crear: `must_change_password = true`.
- **Modal "Resetear Contraseña":**
  - Muestra nombre del usuario y nueva contraseña generada.
  - Checkbox "Enviar nueva contraseña por email".
  - Al resetear: `must_change_password = true`.
- **Acciones en fila:** Editar (ícono lápiz), Resetear pass, (Des)activar usuario.
- **Confirmación al desactivar:** "¿Desactivar a X? No podrá iniciar sesión."
- **Toasts:** Success (verde), Error (rojo).

### 5.6. Cambios a componentes existentes

**RequireAuth.tsx:**
- Redirigir a `/login` (doctores) si no hay token.
- Redirigir a `/change-password` si `must_change_password`.
- Si ruta es `/admin/*` y `role !== "admin"` → página 403.
- Si ruta es `/login` y ya autenticado → redirect según role.
- Si ruta es `/admin` y ya autenticado → redirect a `/admin/users`.

**AuthContext.tsx:**
- Nuevas funciones: `forgotPassword(email)`, `resetPassword(token, newPassword)`.
- Almacenar `portal` (admin/doctor).
- Session type: `{token, role, must_change_password, email, full_name}`.

**AdminLayout.tsx:**
- Sidebar diferente para admin: solo ítems de administración (Users).
- Sin acceso a pacientes, dietas, formularios.

### 5.7. Diseño y Branding

- **Paleta:** Emerald-600 primario (#059669), slate-50 fondo, slate-800 titulos.
- **Componentes:** Button (variants), Card, Badge, Toast, ConfirmModal existentes.
- **Logo:** logo-login.png (login), logo-sidebar.png (sidebar).
- **Iconos:** Phosphor Icons (@phosphor-icons/react).

---

## 6. Email

### 6.1. Email de recuperación de contraseña

**Formato:** Idéntico al template existente en `reminder_service.py`.
- Logo `logo-doctora.jpeg` embebido en base64 inline.
- Fondo `#f8fafc`, tarjeta blanca con `border-radius: 16px`.
- Heading Dra. Acosta en `#065f46`.
- Botón CTA: `background: #10b981`, `border-radius: 999px`, texto blanco.
- Footer: "Dra. Acosta · Nutrición Personalizada".
- Expiración: 30 minutos.

**Parámetros de plantilla:**
- `{{full_name}}` — Nombre del doctor.
- `{{reset_link}}` — URL completa: `APP_URL/reset-password?token=xxx`.

**Asunto:** "Recuperación de Contraseña — Dra. Acosta"

### 6.2. Email de bienvenida (creación de usuario)

**Mismo formato visual.** Parámetros adicionales:
- `{{temp_password}}` — Contraseña temporal generada.
- `{{email}}` — Email del usuario.
- `{{login_link}}` — URL de login.

**Asunto:** "Bienvenido a Nutribot — Dra. Acosta"

### 6.3. Envío

Reutiliza `email_service.send_email_sync(to_email, subject, html_body)` existente (Gmail API OAuth2).

---

## 7. Seguridad

### 7.1. Token de reseteo
- Generación: `secrets.token_urlsafe(32)`.
- Expiración: 30 minutos.
- One-time: `used = true` después de usado.
- Sin reutilización posible.

### 7.2. Respuestas genéricas
- `forgot-password`: Siempre la misma respuesta sin importar si el email existe.
- `verify-reset-token`: No diferenciar entre "token no existe", "expirado", "ya usado".
- `reset-password`: Mismo mensaje de error sin importar la causa del fallo.

### 7.3. Portal validation
- `POST /api/auth/token` valida el rol según el portal.
- Admin no puede loguearse por `/login`, doctor no puede loguearse por `/admin`.

### 7.4. Rate limiting (fuera de alcance inicial — backlog)
No se implementa en esta iteración. Pendiente para futura mejora:
- `POST /api/auth/token`: 5 intentos/minuto por IP.
- `POST /api/auth/forgot-password`: 1 solicitud/2 minutos por email.
- `POST /api/auth/reset-password`: 3 intentos/hora por IP.

---

## 8. Resumen de Archivos a Crear/Modificar

### Backend
| Archivo | Acción |
|---|---|
| `backend/app/models.py` | Agregar modelo `PasswordResetToken` |
| `backend/app/schemas.py` | Agregar schemas `ForgotPasswordRequest`, `ResetPasswordRequest`, `VerifyTokenResponse` |
| `backend/app/api/auth.py` | Agregar endpoints forgot-password, verify-reset-token, reset-password. Modificar token endpoint. |
| `backend/app/api/admin.py` | Modificar creación de doctor: generar contraseña automática |
| `backend/app/core/security.py` | Agregar función `generate_reset_token()` |
| `backend/app/services/email_service.py` | Agregar funciones `send_password_reset_email()`, `send_welcome_email()` |
| `backend/alembic/versions/` | Nueva migración: `password_reset_tokens` |

### Frontend
| Archivo | Acción |
|---|---|
| `frontend/src/pages/AdminLogin.tsx` | Crear |
| `frontend/src/pages/ResetPassword.tsx` | Crear |
| `frontend/src/pages/Login.tsx` | Modificar: + forgot password link/modal, + portal=doctor |
| `frontend/src/pages/AdminUsers.tsx` | Mejorar: modal crear con pass generada, reset, activar/desactivar |
| `frontend/src/context/AuthContext.tsx` | Agregar forgotPassword, resetPassword |
| `frontend/src/components/RequireAuth.tsx` | Agregar validación de admin routes |
| `frontend/src/layouts/AdminLayout.tsx` | Sidebar para admin |
| `frontend/src/services/api.ts` | Agregar endpoints nuevos |
| `frontend/src/App.tsx` | Agregar rutas /admin y /reset-password |

### Infraestructura
| Archivo | Acción |
|---|---|
| `backend/alembic/` | Migración automática |

---

## 9. Flujos Completos

### Flujo A: Admin crea doctor
1. Admin va a `/admin`, se loguea (portal=admin, valida role=admin).
2. Admin va a `/admin/users`, click "Crear Usuario".
3. Llena nombre, email, selecciona rol. Sistema genera contraseña.
4. Admin copia la pass y la entrega al doctor (opcional: enviar email).
5. Doctor va a `/login`, ingresa con su email + pass temporal (portal=doctor).
6. Como `must_change_password=true`, el sistema redirige a `/change-password`.
7. Doctor ingresa contraseña actual + nueva contraseña + confirmación.
8. `POST /api/auth/change-password` → `must_change_password=false`, nuevo JWT.
9. Doctor accede al dashboard.

### Flujo B: Admin resetea contraseña de doctor
1. Admin va a `/admin/users`, busca al doctor, click "Resetear Contraseña".
2. Sistema genera nueva contraseña, la muestra en pantalla.
3. Admin la entrega al doctor. `must_change_password=true`.
4. Doctor sigue el mismo flujo de cambio forzoso (pasos 5-9 del Flujo A).

### Flujo C: Doctor/admin olvida contraseña (auto-recuperación)
1. Usuario va a `/login` (o `/admin`), click "¿Olvidaste tu contraseña?".
2. Ingresa su email. POST /api/auth/forgot-password.
3. Recibe email con link: `APP_URL/reset-password?token=xxx`.
4. Click en link → validación automática del token.
5. Ingresa nueva contraseña + confirmación.
6. POST /api/auth/reset-password → contraseña actualizada.
7. Redirigido a login → inicia sesión con nueva contraseña.

---

## 10. Consideraciones de UX

- **Respuestas genéricas en forgot-password:** No revelar si el email existe o no (previene enumeración de usuarios).
- **Token expirado:** Mensaje claro pero genérico. Botón para volver al login y solicitar uno nuevo.
- **Contraseña generada:** El admin puede regenerar tantas veces como quiera antes de crear el usuario.
- **Estados de carga:** Skeleton loading en tabla de usuarios, spinners en botones de formularios, toasts para feedback.
- **Confirmación en acciones destructivas:** Modal de confirmación para desactivar/resetear usuario.
