# UI/UX Renovación — Implementación

> **Para agentes:** Usar superpowers:subagent-driven-development (recomendado) o superpowers:executing-plans. Pasos usan checkbox (`- [ ]`) para tracking.

**Goal:** Transformar la UI de básica Tailwind a dashboard SaaS profesional tipo Linear/Vercel con lenguaje de médico, sin IDs visibles, y con micro-animaciones.

**Architecture:** 6 fases incrementales. Cada fase produce cambios autocontenidos. La Fase 1 establece la fundación (layout, componentes base). Fases 2-5 rediseñan cada sección. Fase 6 pule estados y responsive.

**Tech Stack:** React 19, TypeScript, Tailwind CSS v4, framer-motion, @phosphor-icons/react, @tanstack/react-query v5, react-router-dom v6

**Spec:** [2026-06-11-ui-ux-renovacion.md](../specs/2026-06-11-ui-ux-renovacion.md)

---

## Estructura de Archivos

### Nuevos
| Archivo | Responsabilidad |
|---------|----------------|
| `frontend/src/components/ui/Skeleton.tsx` | Skeleton loader con shimmer |
| `frontend/src/components/ui/Toast.tsx` | Sistema de toasts (éxito/error/info) |
| `frontend/src/components/ui/EmptyState.tsx` | Estado vacío con icono + texto + acción |
| `frontend/src/components/ui/Badge.tsx` | Badge de estado (variantes de color) |
| `frontend/src/components/ui/Avatar.tsx` | Avatar circular con iniciales + color por nombre |
| `frontend/src/components/ui/Breadcrumbs.tsx` | Breadcrumbs tipo Linear |
| `frontend/src/components/patients/PatientDrawer.tsx` | Drawer lateral para crear/editar paciente |
| `frontend/src/components/patients/PatientRow.tsx` | Fila de paciente en lista (avatar + datos + acciones) |
| `frontend/src/components/patients/WeightSparkline.tsx` | Mini gráfico de peso en perfil |
| `frontend/src/components/patients/MetricsModal.tsx` | Modal para registrar métricas |
| `frontend/src/components/sharing/ShareModal.tsx` | Modal de compartir formulario |
| `frontend/src/components/dashboard/KpiCard.tsx` | Tarjeta KPI del dashboard |
| `frontend/src/components/dashboard/ActivityTimeline.tsx` | Timeline de actividad reciente |
| `frontend/src/components/dashboard/ProfileProgress.tsx` | Barra de progreso de perfiles |
| `frontend/src/context/ToastContext.tsx` | Contexto para sistema de toasts |

### Modificados
| Archivo | Cambio |
|---------|--------|
| `frontend/package.json` | Agregar framer-motion, @phosphor-icons/react |
| `frontend/src/types/index.ts` | Tipos nuevos, feature flags |
| `frontend/src/App.tsx` | Ruta `/formularios`, redirect de `/intake-links` |
| `frontend/src/layouts/AdminLayout.tsx` | Sidebar Phosphor, top bar, breadcrumbs |
| `frontend/src/pages/Dashboard.tsx` | Bento grid KPI + timeline + progreso |
| `frontend/src/pages/Patients.tsx` | Avatares, estados legibles, drawer crear |
| `frontend/src/pages/PatientDetail.tsx` | Sin tabs, vista única scrollable |
| `frontend/src/pages/Diets.tsx` | Sin IDs, badges legibles, búsqueda nombre |
| `frontend/src/pages/DietWizard.tsx` | Búsqueda por nombre paso 1, bloqueo perfil |
| `frontend/src/pages/DietDetail.tsx` | Mostrar nombre paciente, no ID |
| `frontend/src/pages/IntakeLinks.tsx` | Renombrar a Formularios, rediseñar |
| `frontend/src/components/ShareButtons.tsx` | Integrar en modal nuevo |
| `frontend/src/components/wizard/PatientSearchInput.tsx` | Mostrar nombres + ciudad, no IDs |
| `frontend/src/components/diet/DietPreviewPanel.tsx` | Mostrar nombre paciente, no ID |

---

## Fase 1: Fundación

### Task 1.1: Instalar dependencias

**Files:** Modify: `frontend/package.json`

- [ ] **Step 1: Instalar framer-motion y phosphor-icons**

```bash
cd frontend && npm install framer-motion @phosphor-icons/react
```

- [ ] **Step 2: Verificar instalación**

```bash
cd frontend && npm ls framer-motion @phosphor-icons/react
```

Expected: ambas listadas con versión

- [ ] **Step 3: Commit**

```bash
git add frontend/package.json frontend/package-lock.json
git commit -m "chore: add framer-motion and @phosphor-icons/react dependencies"
```

---

### Task 1.2: Componentes base — Avatar y Badge

**Files:** Create: `frontend/src/components/ui/Avatar.tsx`, `frontend/src/components/ui/Badge.tsx`

- [ ] **Step 1: Crear Avatar.tsx**

```tsx
// frontend/src/components/ui/Avatar.tsx
import { useMemo } from "react";

const AVATAR_COLORS = [
  "bg-emerald-100 text-emerald-700",
  "bg-sky-100 text-sky-700",
  "bg-violet-100 text-violet-700",
  "bg-amber-100 text-amber-700",
  "bg-rose-100 text-rose-700",
  "bg-cyan-100 text-cyan-700",
  "bg-indigo-100 text-indigo-700",
  "bg-teal-100 text-teal-700",
];

function hashName(name: string): number {
  let hash = 0;
  for (let i = 0; i < name.length; i++) {
    hash = name.charCodeAt(i) + ((hash << 5) - hash);
  }
  return Math.abs(hash);
}

function getInitials(firstName?: string | null, lastName?: string | null): string {
  const f = firstName?.charAt(0)?.toUpperCase() ?? "";
  const l = lastName?.charAt(0)?.toUpperCase() ?? "";
  return f + l || "?";
}

type AvatarProps = {
  firstName?: string | null;
  lastName?: string | null;
  size?: "sm" | "md" | "lg";
};

export function Avatar({ firstName, lastName, size = "md" }: AvatarProps) {
  const initials = useMemo(() => getInitials(firstName, lastName), [firstName, lastName]);
  const colorClass = useMemo(() => {
    const name = (firstName ?? "") + (lastName ?? "");
    return AVATAR_COLORS[hashName(name) % AVATAR_COLORS.length];
  }, [firstName, lastName]);

  const sizeClasses = {
    sm: "w-8 h-8 text-xs",
    md: "w-10 h-10 text-sm",
    lg: "w-16 h-16 text-xl",
  };

  return (
    <div
      className={`${sizeClasses[size]} ${colorClass} rounded-full flex items-center justify-center font-semibold shrink-0`}
      aria-hidden="true"
    >
      {initials}
    </div>
  );
}
```

- [ ] **Step 2: Crear Badge.tsx**

```tsx
// frontend/src/components/ui/Badge.tsx
import type { ReactNode } from "react";

const VARIANTS = {
  success: "bg-emerald-50 text-emerald-700 ring-emerald-600/20",
  warning: "bg-amber-50 text-amber-700 ring-amber-600/20",
  danger: "bg-red-50 text-red-700 ring-red-600/20",
  neutral: "bg-slate-50 text-slate-600 ring-slate-500/20",
  info: "bg-sky-50 text-sky-700 ring-sky-600/20",
} as const;

type BadgeVariant = keyof typeof VARIANTS;

type BadgeProps = {
  children: ReactNode;
  variant?: BadgeVariant;
};

export function Badge({ children, variant = "neutral" }: BadgeProps) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ring-1 ring-inset ${VARIANTS[variant]}`}
    >
      {children}
    </span>
  );
}
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/ui/Avatar.tsx frontend/src/components/ui/Badge.tsx
git commit -m "feat: add Avatar and Badge base components"
```

---

### Task 1.3: Componentes base — Skeleton, EmptyState, Toast

**Files:** Create: `frontend/src/components/ui/Skeleton.tsx`, `frontend/src/components/ui/EmptyState.tsx`, `frontend/src/components/ui/Toast.tsx`, `frontend/src/context/ToastContext.tsx`

- [ ] **Step 1: Crear Skeleton.tsx**

```tsx
// frontend/src/components/ui/Skeleton.tsx
type SkeletonProps = {
  className?: string;
};

export function Skeleton({ className = "" }: SkeletonProps) {
  return (
    <div
      className={`animate-pulse rounded-lg bg-slate-200 ${className}`}
      aria-hidden="true"
    />
  );
}

export function SkeletonRow() {
  return (
    <div className="flex items-center gap-3 p-4">
      <Skeleton className="w-10 h-10 rounded-full" />
      <div className="flex-1 space-y-2">
        <Skeleton className="h-4 w-1/3" />
        <Skeleton className="h-3 w-1/4" />
      </div>
    </div>
  );
}

export function SkeletonCard() {
  return (
    <div className="bg-white rounded-2xl p-6 space-y-3">
      <Skeleton className="h-4 w-1/4" />
      <Skeleton className="h-8 w-1/2" />
      <Skeleton className="h-3 w-3/4" />
    </div>
  );
}
```

- [ ] **Step 2: Crear EmptyState.tsx**

```tsx
// frontend/src/components/ui/EmptyState.tsx
import type { ReactNode } from "react";

type EmptyStateProps = {
  icon?: ReactNode;
  title: string;
  description?: string;
  action?: ReactNode;
};

export function EmptyState({ icon, title, description, action }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-16 px-4 text-center">
      {icon && <div className="text-slate-300 mb-4">{icon}</div>}
      <h3 className="text-lg font-semibold text-slate-700">{title}</h3>
      {description && (
        <p className="mt-1 text-sm text-slate-500 max-w-sm">{description}</p>
      )}
      {action && <div className="mt-6">{action}</div>}
    </div>
  );
}
```

- [ ] **Step 3: Crear ToastContext.tsx**

```tsx
// frontend/src/context/ToastContext.tsx
import { createContext, useContext, useState, useCallback, type ReactNode } from "react";

type ToastType = "success" | "error" | "info";

type Toast = {
  id: number;
  message: string;
  type: ToastType;
};

type ToastContextValue = {
  toasts: Toast[];
  addToast: (message: string, type?: ToastType) => void;
  removeToast: (id: number) => void;
};

const ToastContext = createContext<ToastContextValue | null>(null);

let nextId = 0;

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const removeToast = useCallback((id: number) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const addToast = useCallback(
    (message: string, type: ToastType = "success") => {
      const id = nextId++;
      setToasts((prev) => [...prev, { id, message, type }]);
      setTimeout(() => removeToast(id), 4000);
    },
    [removeToast]
  );

  return (
    <ToastContext.Provider value={{ toasts, addToast, removeToast }}>
      {children}
    </ToastContext.Provider>
  );
}

export function useToast() {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error("useToast must be used within ToastProvider");
  return ctx;
}
```

- [ ] **Step 4: Crear Toast.tsx (renderizado)**

```tsx
// frontend/src/components/ui/Toast.tsx
import { useToast } from "../../context/ToastContext";
import { X } from "@phosphor-icons/react";
import { AnimatePresence, motion } from "framer-motion";

const TYPE_STYLES = {
  success: "bg-emerald-600 text-white",
  error: "bg-red-600 text-white",
  info: "bg-slate-800 text-white",
};

export function ToastContainer() {
  const { toasts, removeToast } = useToast();

  return (
    <div className="fixed bottom-4 right-4 z-[100] flex flex-col gap-2 pointer-events-none">
      <AnimatePresence>
        {toasts.map((toast) => (
          <motion.div
            key={toast.id}
            initial={{ opacity: 0, y: 24, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -8, scale: 0.95 }}
            transition={{ duration: 0.25, ease: [0.16, 1, 0.3, 1] }}
            className={`pointer-events-auto rounded-xl px-4 py-3 text-sm font-medium shadow-lg flex items-center gap-3 ${TYPE_STYLES[toast.type]}`}
          >
            <span>{toast.message}</span>
            <button
              onClick={() => removeToast(toast.id)}
              className="shrink-0 hover:opacity-70"
              aria-label="Cerrar"
            >
              <X size={16} weight="bold" />
            </button>
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  );
}
```

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/ui/Skeleton.tsx frontend/src/components/ui/EmptyState.tsx frontend/src/components/ui/Toast.tsx frontend/src/context/ToastContext.tsx
git commit -m "feat: add Skeleton, EmptyState, and Toast base components"
```

---

### Task 1.4: Refactor AdminLayout — Sidebar + TopBar + Breadcrumbs

**Files:** 
- Modify: `frontend/src/layouts/AdminLayout.tsx`
- Modify: `frontend/src/main.tsx` (wrap with ToastProvider)

- [ ] **Step 1: Wrap app con ToastProvider en main.tsx**

Read `frontend/src/main.tsx` first to see current structure.

Modify `frontend/src/main.tsx`:
```tsx
import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { AuthProvider } from "./context/AuthContext";
import { ToastProvider } from "./context/ToastContext";
import App from "./App";
import "./index.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <BrowserRouter>
      <ToastProvider>
        <AuthProvider>
          <App />
        </AuthProvider>
      </ToastProvider>
    </BrowserRouter>
  </React.StrictMode>
);
```

- [ ] **Step 2: Reescribir AdminLayout con sidebar Phosphor + top bar + breadcrumbs**

Read current `frontend/src/layouts/AdminLayout.tsx` to understand existing mobile/desktop logic.

Create the new version (see complete code below):

```tsx
// frontend/src/layouts/AdminLayout.tsx
import { useState, useEffect } from "react";
import { Link, Outlet, useLocation, useNavigate } from "react-router-dom";
import { AnimatePresence, motion } from "framer-motion";
import {
  House,
  Users,
  BowlFood,
  LinkSimple,
  Gear,
  SignOut,
  List,
  X,
  UserCircle,
  CaretRight,
} from "@phosphor-icons/react";
import { useAuth } from "../context/AuthContext";
import { useToast } from "../context/ToastContext";
import { ToastContainer } from "../components/ui/Toast";
import { Avatar } from "../components/ui/Avatar";

const NAV_ITEMS = [
  { to: "/dashboard", label: "Dashboard", icon: House },
  { to: "/patients", label: "Pacientes", icon: Users },
  { to: "/diets", label: "Dietas", icon: BowlFood },
  { to: "/formularios", label: "Formularios", icon: LinkSimple },
];

const ADMIN_ITEM = { to: "/admin/users", label: "Administración", icon: Gear };

const BREADCRUMB_LABELS: Record<string, string> = {
  dashboard: "Dashboard",
  patients: "Pacientes",
  diets: "Dietas",
  "diets/new": "Nueva Dieta",
  formularios: "Formularios",
  "intake-links": "Formularios",
  "admin/users": "Administración",
  telegram: "Telegram",
};

function getBreadcrumbs(pathname: string) {
  const segments = pathname.split("/").filter(Boolean);
  const crumbs: { label: string; to: string }[] = [];
  let accumulated = "";
  for (const seg of segments) {
    accumulated += "/" + seg;
    const label = BREADCRUMB_LABELS[seg] || seg;
    crumbs.push({ label, to: accumulated });
  }
  return crumbs;
}

export default function AdminLayout() {
  const { session, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);

  useEffect(() => {
    setSidebarOpen(false);
  }, [location.pathname]);

  const isActive = (to: string) => {
    if (to === "/dashboard") return location.pathname === "/dashboard";
    return location.pathname.startsWith(to);
  };

  const breadcrumbs = getBreadcrumbs(location.pathname);
  const doctorName = session?.full_name ?? "Doctor";
  const doctorEmail = session?.email ?? "";

  const navItems = session?.role === "admin" ? [...NAV_ITEMS, ADMIN_ITEM] : NAV_ITEMS;

  return (
    <div className="min-h-[100dvh] bg-slate-50 flex">
      {/* Sidebar - Desktop */}
      <aside className="hidden md:flex flex-col w-60 bg-white border-r border-slate-200 shrink-0">
        {/* Logo */}
        <div className="p-4 border-b border-slate-100">
          <Link to="/dashboard" className="flex items-center gap-2.5">
            <img src="/logo-nutribot.svg" alt="Logo" className="w-8 h-8" />
            <span className="text-sm font-semibold text-slate-800 leading-tight">
              Nutribot
            </span>
          </Link>
        </div>

        {/* Nav */}
        <nav className="flex-1 p-3 space-y-0.5 overflow-y-auto">
          {navItems.map((item) => {
            const Icon = item.icon;
            const active = isActive(item.to);
            return (
              <Link
                key={item.to}
                to={item.to}
                className={`flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-colors duration-150 ${
                  active
                    ? "bg-emerald-50 text-emerald-700"
                    : "text-slate-600 hover:bg-slate-50 hover:text-slate-800"
                }`}
              >
                <Icon size={20} weight={active ? "fill" : "regular"} />
                {item.label}
              </Link>
            );
          })}
        </nav>

        {/* Footer */}
        <div className="p-3 border-t border-slate-100">
          <button
            onClick={logout}
            className="flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium text-slate-500 hover:bg-red-50 hover:text-red-600 w-full transition-colors duration-150"
          >
            <SignOut size={20} />
            Cerrar sesión
          </button>
        </div>
      </aside>

      {/* Main */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Top Bar */}
        <header className="sticky top-0 z-30 bg-white/80 backdrop-blur-md border-b border-slate-200">
          <div className="flex items-center justify-between h-14 px-4 md:px-6">
            {/* Left: mobile menu + breadcrumbs */}
            <div className="flex items-center gap-3 min-w-0">
              <button
                onClick={() => setSidebarOpen(true)}
                className="md:hidden p-1.5 -ml-1.5 rounded-lg text-slate-600 hover:bg-slate-100"
                aria-label="Abrir menú"
              >
                <List size={22} />
              </button>
              {/* Breadcrumbs */}
              <nav className="hidden sm:flex items-center gap-1.5 text-sm min-w-0">
                {breadcrumbs.map((crumb, i) => (
                  <span key={crumb.to} className="flex items-center gap-1.5 min-w-0">
                    {i > 0 && <CaretRight size={12} className="text-slate-300 shrink-0" weight="bold" />}
                    {i === breadcrumbs.length - 1 ? (
                      <span className="text-slate-800 font-medium truncate">{crumb.label}</span>
                    ) : (
                      <Link to={crumb.to} className="text-slate-500 hover:text-slate-700 truncate">
                        {crumb.label}
                      </Link>
                    )}
                  </span>
                ))}
              </nav>
            </div>

            {/* Right: doctor */}
            <div className="relative">
              <button
                onClick={() => setUserMenuOpen(!userMenuOpen)}
                className="flex items-center gap-2 p-1.5 rounded-xl hover:bg-slate-100 transition-colors"
              >
                <Avatar firstName={doctorName} lastName="" size="sm" />
                <span className="hidden sm:block text-sm font-medium text-slate-700 truncate max-w-[120px]">
                  {doctorName}
                </span>
              </button>

              {/* User dropdown */}
              <AnimatePresence>
                {userMenuOpen && (
                  <>
                    <div
                      className="fixed inset-0 z-40"
                      onClick={() => setUserMenuOpen(false)}
                    />
                    <motion.div
                      initial={{ opacity: 0, y: -8, scale: 0.96 }}
                      animate={{ opacity: 1, y: 0, scale: 1 }}
                      exit={{ opacity: 0, y: -8, scale: 0.96 }}
                      transition={{ duration: 0.15, ease: [0.16, 1, 0.3, 1] }}
                      className="absolute right-0 top-full mt-1 w-56 bg-white rounded-xl shadow-lg border border-slate-200 z-50 py-1"
                    >
                      <div className="px-3 py-2 border-b border-slate-100">
                        <p className="text-sm font-medium text-slate-800">{doctorName}</p>
                        <p className="text-xs text-slate-500 truncate">{doctorEmail}</p>
                      </div>
                      <button
                        onClick={logout}
                        className="w-full text-left px-3 py-2 text-sm text-slate-600 hover:bg-red-50 hover:text-red-600 flex items-center gap-2"
                      >
                        <SignOut size={16} />
                        Cerrar sesión
                      </button>
                    </motion.div>
                  </>
                )}
              </AnimatePresence>
            </div>
          </div>
        </header>

        {/* Content */}
        <main className="flex-1 p-4 md:p-6 lg:p-8 max-w-[1400px] mx-auto w-full">
          <Outlet />
        </main>
      </div>

      {/* Mobile sidebar overlay */}
      <AnimatePresence>
        {sidebarOpen && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.2 }}
              className="fixed inset-0 bg-black/30 backdrop-blur-sm z-40 md:hidden"
              onClick={() => setSidebarOpen(false)}
            />
            <motion.aside
              initial={{ x: "-100%" }}
              animate={{ x: 0 }}
              exit={{ x: "-100%" }}
              transition={{ duration: 0.25, ease: [0.16, 1, 0.3, 1] }}
              className="fixed left-0 top-0 bottom-0 w-64 bg-white border-r border-slate-200 z-50 flex flex-col md:hidden"
            >
              <div className="flex items-center justify-between p-4 border-b border-slate-100">
                <Link to="/dashboard" className="flex items-center gap-2.5">
                  <img src="/logo-nutribot.svg" alt="Logo" className="w-7 h-7" />
                  <span className="text-sm font-semibold text-slate-800">Nutribot</span>
                </Link>
                <button
                  onClick={() => setSidebarOpen(false)}
                  className="p-1.5 rounded-lg text-slate-500 hover:bg-slate-100"
                  aria-label="Cerrar menú"
                >
                  <X size={20} />
                </button>
              </div>
              <nav className="flex-1 p-3 space-y-0.5 overflow-y-auto">
                {navItems.map((item) => {
                  const Icon = item.icon;
                  const active = isActive(item.to);
                  return (
                    <Link
                      key={item.to}
                      to={item.to}
                      className={`flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-colors duration-150 ${
                        active
                          ? "bg-emerald-50 text-emerald-700"
                          : "text-slate-600 hover:bg-slate-50 hover:text-slate-800"
                      }`}
                    >
                      <Icon size={20} weight={active ? "fill" : "regular"} />
                      {item.label}
                    </Link>
                  );
                })}
              </nav>
              <div className="p-3 border-t border-slate-100">
                <button
                  onClick={logout}
                  className="flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium text-slate-500 hover:bg-red-50 hover:text-red-600 w-full transition-colors"
                >
                  <SignOut size={20} />
                  Cerrar sesión
                </button>
              </div>
            </motion.aside>
          </>
        )}
      </AnimatePresence>

      {/* Toasts */}
      <ToastContainer />
    </div>
  );
}
```

- [ ] **Step 3: Actualizar types/index.ts con feature flags**

Agregar al final de `frontend/src/types/index.ts`:
```ts
// --- Feature flags ---
export const NEXT_FEATURES = {
  batchDiets: false,
  darkMode: false,
} as const;
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/layouts/AdminLayout.tsx frontend/src/main.tsx frontend/src/types/index.ts
git commit -m "feat: redesign AdminLayout with Phosphor icons, top bar, breadcrumbs, and mobile drawer"
```

---

### Task 1.5: Agregar ruta /formularios y redirect

**Files:** Modify: `frontend/src/App.tsx`

- [ ] **Step 1: Leer App.tsx actual**

Read `frontend/src/App.tsx` para ver rutas existentes.

- [ ] **Step 2: Agregar ruta /formularios y redirect de /intake-links**

En `App.tsx`, dentro de las rutas protegidas, agregar:
```tsx
// Redirect de URL antigua a nueva
<Route path="/intake-links" element={<Navigate to="/formularios" replace />} />
<Route path="/intake-links/:token" element={<Navigate to="/formularios/:token" replace />} />
// Nueva ruta
<Route path="/formularios" element={<IntakeLinks />} />
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/App.tsx
git commit -m "feat: add /formularios route with redirect from /intake-links"
```

---

## Fase 2: Dashboard

### Task 2.1: Dashboard — KpiCard, ActivityTimeline, ProfileProgress

**Files:**
- Create: `frontend/src/components/dashboard/KpiCard.tsx`
- Create: `frontend/src/components/dashboard/ActivityTimeline.tsx`
- Create: `frontend/src/components/dashboard/ProfileProgress.tsx`
- Modify: `frontend/src/pages/Dashboard.tsx`

- [ ] **Step 1: Crear KpiCard.tsx**

```tsx
// frontend/src/components/dashboard/KpiCard.tsx
import type { ReactNode } from "react";

type KpiCardProps = {
  label: string;
  value: string | number;
  trend?: { direction: "up" | "down"; value: string };
  icon: ReactNode;
};

export function KpiCard({ label, value, trend, icon }: KpiCardProps) {
  return (
    <div className="bg-white rounded-2xl p-6 shadow-[0_20px_40px_-15px_rgba(0,0,0,0.05)]">
      <div className="flex items-center justify-between mb-4">
        <span className="text-sm font-medium text-slate-500">{label}</span>
        <span className="text-slate-300">{icon}</span>
      </div>
      <p className="text-4xl font-mono tracking-tight font-semibold text-slate-800 tabular-nums">
        {value}
      </p>
      {trend && (
        <p
          className={`mt-2 text-sm font-medium ${
            trend.direction === "up" ? "text-emerald-600" : "text-red-500"
          }`}
        >
          {trend.direction === "up" ? "↑" : "↓"} {trend.value}
        </p>
      )}
    </div>
  );
}
```

- [ ] **Step 2: Crear ActivityTimeline.tsx**

```tsx
// frontend/src/components/dashboard/ActivityTimeline.tsx
import { Avatar } from "../ui/Avatar";

type Activity = Record<string, unknown> & {
  action?: string;
  entity_type?: string;
  doctor_name?: string;
  patient_name?: string;
  created_at?: string;
};

function timeAgo(dateStr: string): string {
  const now = Date.now();
  const then = new Date(dateStr).getTime();
  const diffMin = Math.floor((now - then) / 60000);
  if (diffMin < 1) return "Ahora mismo";
  if (diffMin < 60) return `Hace ${diffMin} min`;
  const diffHrs = Math.floor(diffMin / 60);
  if (diffHrs < 24) return `Hace ${diffHrs} h`;
  const diffDays = Math.floor(diffHrs / 24);
  if (diffDays < 7) return `Hace ${diffDays} días`;
  return new Date(dateStr).toLocaleDateString("es-VE", {
    day: "numeric",
    month: "short",
  });
}

function describeAction(a: Activity): string {
  const action = (a.action as string) ?? "";
  const patient = (a.patient_name as string) ?? "paciente";
  if (action.includes("diet")) return `Dieta generada para ${patient}`;
  if (action.includes("patient")) return `Paciente ${patient} creado`;
  if (action.includes("intake")) return `Formulario enviado a ${patient}`;
  if (action.includes("metric")) return `Métricas registradas para ${patient}`;
  return `${action} — ${patient}`;
}

export function ActivityTimeline({ activities }: { activities: Activity[] }) {
  if (!activities.length) {
    return (
      <div className="text-center py-8 text-sm text-slate-500">
        No hay actividad reciente
      </div>
    );
  }

  return (
    <div className="space-y-1 max-h-[400px] overflow-y-auto">
      {activities.slice(0, 10).map((a, i) => (
        <div
          key={i}
          className="flex items-center gap-3 px-2 py-2.5 rounded-xl hover:bg-slate-50 transition-colors"
        >
          <Avatar
            firstName={(a.patient_name as string) ?? "?"}
            lastName=""
            size="sm"
          />
          <div className="flex-1 min-w-0">
            <p className="text-sm text-slate-700 truncate">{describeAction(a)}</p>
          </div>
          <span className="text-xs text-slate-400 shrink-0">
            {a.created_at ? timeAgo(a.created_at as string) : ""}
          </span>
        </div>
      ))}
    </div>
  );
}
```

- [ ] **Step 3: Crear ProfileProgress.tsx**

```tsx
// frontend/src/components/dashboard/ProfileProgress.tsx
type ProfileProgressProps = {
  total: number;
  complete: number;
  incomplete: number;
};

export function ProfileProgress({ total, complete, incomplete }: ProfileProgressProps) {
  const pct = total > 0 ? Math.round((complete / total) * 100) : 0;

  return (
    <div className="space-y-4">
      <div>
        <div className="flex items-baseline justify-between mb-2">
          <span className="text-2xl font-mono font-semibold text-slate-800 tracking-tight tabular-nums">
            {complete}
          </span>
          <span className="text-sm text-slate-500">de {total}</span>
        </div>
        <p className="text-sm text-slate-500 mb-3">{pct}% completados</p>
        {/* Progress bar */}
        <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
          <div
            className="h-full bg-emerald-500 rounded-full transition-all duration-700 ease-[cubic-bezier(0.16,1,0.3,1)]"
            style={{ width: `${pct}%` }}
          />
        </div>
      </div>
      {/* Legend */}
      <div className="flex gap-4 text-sm">
        <div className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full bg-emerald-500" />
          <span className="text-slate-600">{complete} Completos</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full bg-amber-400" />
          <span className="text-slate-600">{incomplete} Pendientes</span>
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 4: Reescribir Dashboard.tsx con Bento Grid**

Leer `frontend/src/pages/Dashboard.tsx` actual para ver la llamada API existente.

```tsx
// frontend/src/pages/Dashboard.tsx
import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { Users, UserPlus, ClipboardText, BowlFood } from "@phosphor-icons/react";
import { motion } from "framer-motion";
import { getDashboardSummary } from "../services/api";
import { KpiCard } from "../components/dashboard/KpiCard";
import { ActivityTimeline } from "../components/dashboard/ActivityTimeline";
import { ProfileProgress } from "../components/dashboard/ProfileProgress";
import { SkeletonCard } from "../components/ui/Skeleton";
import type { DashboardSummary } from "../types";

export default function Dashboard() {
  const [data, setData] = useState<DashboardSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await getDashboardSummary();
      setData(result);
    } catch (err) {
      setError("No se pudo cargar el resumen. Intenta de nuevo.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  if (error) {
    return (
      <div className="text-center py-16">
        <p className="text-red-600 text-sm mb-4">{error}</p>
        <button
          onClick={fetchData}
          className="px-4 py-2 bg-emerald-600 text-white rounded-full text-sm font-medium hover:bg-emerald-700 transition-colors"
        >
          Reintentar
        </button>
      </div>
    );
  }

  const container = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: { staggerChildren: 0.1 },
    },
  };

  const item = {
    hidden: { opacity: 0, y: 24 },
    show: { opacity: 1, y: 0, transition: { duration: 0.5, ease: [0.16, 1, 0.3, 1] } },
  };

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold text-slate-800 md:hidden">Dashboard</h1>

      {/* KPIs */}
      <motion.div
        variants={container}
        initial="hidden"
        animate="show"
        className="grid grid-cols-2 lg:grid-cols-4 gap-4"
      >
        <motion.div variants={item}>
          {loading ? (
            <SkeletonCard />
          ) : (
            <KpiCard
              label="Total pacientes"
              value={data?.total_patients ?? 0}
              icon={<Users size={22} />}
            />
          )}
        </motion.div>
        <motion.div variants={item}>
          {loading ? (
            <SkeletonCard />
          ) : (
            <KpiCard
              label="Nuevos este mes"
              value={data?.new_patients_30d ?? 0}
              icon={<UserPlus size={22} />}
            />
          )}
        </motion.div>
        <motion.div variants={item}>
          {loading ? (
            <SkeletonCard />
          ) : (
            <KpiCard
              label="Perfiles incompletos"
              value={data?.incomplete_profiles ?? 0}
              icon={<ClipboardText size={22} />}
            />
          )}
        </motion.div>
        <motion.div variants={item}>
          {loading ? (
            <SkeletonCard />
          ) : (
            <KpiCard
              label="Dietas generadas"
              value={data?.diets_generated ?? 0}
              icon={<BowlFood size={22} />}
            />
          )}
        </motion.div>
      </motion.div>

      {/* Bottom row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Activity timeline */}
        <motion.div
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.4, ease: [0.16, 1, 0.3, 1] }}
          className="lg:col-span-2 bg-white rounded-2xl p-6 shadow-[0_20px_40px_-15px_rgba(0,0,0,0.05)]"
        >
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold text-slate-800">Actividad reciente</h2>
            <Link
              to="/patients"
              className="text-xs font-medium text-emerald-600 hover:text-emerald-700"
            >
              Ver todos →
            </Link>
          </div>
          {loading ? (
            <div className="space-y-3">
              {[...Array(4)].map((_, i) => (
                <div key={i} className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-full bg-slate-200 animate-pulse" />
                  <div className="flex-1 space-y-1.5">
                    <div className="h-3 bg-slate-200 rounded animate-pulse w-2/3" />
                    <div className="h-2 bg-slate-100 rounded animate-pulse w-1/4" />
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <ActivityTimeline activities={data?.latest_activity ?? []} />
          )}
        </motion.div>

        {/* Profile progress */}
        <motion.div
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.5, ease: [0.16, 1, 0.3, 1] }}
          className="bg-white rounded-2xl p-6 shadow-[0_20px_40px_-15px_rgba(0,0,0,0.05)]"
        >
          <h2 className="text-sm font-semibold text-slate-800 mb-4">
            Perfiles completados
          </h2>
          {loading ? (
            <div className="space-y-3">
              <div className="h-6 bg-slate-200 rounded animate-pulse w-1/2" />
              <div className="h-2 bg-slate-100 rounded-full animate-pulse" />
              <div className="h-3 bg-slate-100 rounded animate-pulse w-3/4" />
            </div>
          ) : (
            <ProfileProgress
              total={data?.total_patients ?? 0}
              complete={(data?.total_patients ?? 0) - (data?.incomplete_profiles ?? 0)}
              incomplete={data?.incomplete_profiles ?? 0}
            />
          )}
        </motion.div>
      </div>
    </div>
  );
}
```

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/dashboard/ frontend/src/pages/Dashboard.tsx
git commit -m "feat: redesign Dashboard with KPI bento grid, activity timeline, and profile progress"
```

---

## Fase 3: Pacientes

### Task 3.1: PatientRow — Fila de paciente amigable

**Files:** Create: `frontend/src/components/patients/PatientRow.tsx`

- [ ] **Step 1: Crear PatientRow.tsx**

```tsx
// frontend/src/components/patients/PatientRow.tsx
import { Link } from "react-router-dom";
import { DotsThree, User, BowlFood, Envelope, Pencil } from "@phosphor-icons/react";
import { useState, useRef, useEffect } from "react";
import { Avatar } from "../ui/Avatar";
import { Badge } from "../ui/Badge";
import type { Patient, PatientSummary } from "../../types";

type PatientRowProps = {
  patient: Patient;
  summary?: PatientSummary | null;
  onShare?: (patient: Patient) => void;
};

function describeStatus(
  p: Patient,
  s?: PatientSummary | null
): { label: string; variant: "success" | "warning" | "info" | "neutral" } {
  if (p.is_archived) return { label: "Archivado", variant: "neutral" };
  if (s?.latest_diet) {
    const daysAgo = Math.floor(
      (Date.now() - new Date(s.latest_diet.created_at).getTime()) / 86400000
    );
    if (daysAgo <= 0) return { label: "Dieta activa hoy", variant: "success" };
    if (daysAgo === 1) return { label: "Dieta activa ayer", variant: "success" };
    return { label: `Dieta activa hace ${daysAgo} días`, variant: "success" };
  }
  if (!s?.profile_flags?.is_profile_complete)
    return { label: "Perfil incompleto", variant: "warning" };
  return { label: "Sin dieta aún", variant: "info" };
}

export function PatientRow({ patient, summary, onShare }: PatientRowProps) {
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setMenuOpen(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  const status = describeStatus(patient, summary);

  return (
    <div className="flex items-center gap-4 px-4 py-3 hover:bg-slate-50 transition-colors group">
      <Avatar firstName={patient.first_name} lastName={patient.last_name} size="md" />
      <div className="flex-1 min-w-0">
        <Link
          to={`/patients/${patient.id}`}
          className="text-sm font-medium text-slate-800 hover:text-emerald-600 truncate block"
        >
          {patient.first_name} {patient.last_name}
        </Link>
        <p className="text-xs text-slate-500 truncate">{patient.city ?? "Sin ciudad"}</p>
      </div>
      <Badge variant={status.variant}>{status.label}</Badge>
      {/* Actions menu */}
      <div className="relative" ref={menuRef}>
        <button
          onClick={() => setMenuOpen(!menuOpen)}
          className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100 opacity-0 group-hover:opacity-100 transition-all"
          aria-label="Acciones"
        >
          <DotsThree size={18} weight="bold" />
        </button>
        {menuOpen && (
          <div className="absolute right-0 top-full mt-1 w-52 bg-white rounded-xl shadow-lg border border-slate-200 z-50 py-1">
            <Link
              to={`/patients/${patient.id}`}
              className="flex items-center gap-2 px-3 py-2 text-sm text-slate-600 hover:bg-slate-50"
              onClick={() => setMenuOpen(false)}
            >
              <User size={16} /> Ver perfil
            </Link>
            <Link
              to={`/diets/new?patient=${patient.id}`}
              className="flex items-center gap-2 px-3 py-2 text-sm text-slate-600 hover:bg-slate-50"
              onClick={() => setMenuOpen(false)}
            >
              <BowlFood size={16} /> Nueva dieta
            </Link>
            <button
              onClick={() => {
                setMenuOpen(false);
                onShare?.(patient);
              }}
              className="flex items-center gap-2 px-3 py-2 text-sm text-slate-600 hover:bg-slate-50 w-full text-left"
            >
              <Envelope size={16} /> Enviar formulario
            </button>
            <Link
              to={`/patients/${patient.id}`}
              className="flex items-center gap-2 px-3 py-2 text-sm text-slate-600 hover:bg-slate-50"
              onClick={() => setMenuOpen(false)}
            >
              <Pencil size={16} /> Editar datos
            </Link>
          </div>
        )}
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/patients/PatientRow.tsx
git commit -m "feat: add PatientRow with avatar, human-readable status, and contextual menu"
```

---

### Task 3.2: PatientDrawer — Crear paciente completo

**Files:** Create: `frontend/src/components/patients/PatientDrawer.tsx`

- [ ] **Step 1: Crear PatientDrawer.tsx**

Este componente es un drawer lateral con formulario completo. Lee las APIs existentes en `frontend/src/services/api.ts` para usar `createPatient`, `PUT` y `POST` de profile y metrics.

```tsx
// frontend/src/components/patients/PatientDrawer.tsx
import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, CaretDown, CaretUp } from "@phosphor-icons/react";
import { createPatient } from "../../services/api";
import { useToast } from "../../context/ToastContext";
import type { Patient } from "../../types";

type PatientFormData = {
  first_name: string;
  last_name: string;
  birth_date: string;
  sex: string;
  country: string;
  city: string;
  whatsapp: string;
  email: string;
  objective: string;
  diseases: string;
  medications: string;
  food_allergies: string;
  foods_avoided: string;
  dietary_style: string;
  weight_kg: string;
  height_cm: string;
};

const EMPTY_FORM: PatientFormData = {
  first_name: "",
  last_name: "",
  birth_date: "",
  sex: "",
  country: "",
  city: "",
  whatsapp: "",
  email: "",
  objective: "",
  diseases: "",
  medications: "",
  food_allergies: "",
  foods_avoided: "",
  dietary_style: "",
  weight_kg: "",
  height_cm: "",
};

const OBJECTIVES = [
  { value: "", label: "Seleccionar..." },
  { value: "fat_loss", label: "Pérdida de grasa" },
  { value: "muscle_gain", label: "Ganancia muscular" },
  { value: "maintenance", label: "Mantenimiento" },
  { value: "health_improvement", label: "Mejora de salud" },
  { value: "sports_performance", label: "Rendimiento deportivo" },
];

const DIETARY_STYLES = [
  { value: "", label: "Seleccionar..." },
  { value: "omnivore", label: "Omnívoro" },
  { value: "vegetarian", label: "Vegetariano" },
  { value: "vegan", label: "Vegano" },
  { value: "pescatarian", label: "Pescetariano" },
  { value: "keto", label: "Keto" },
  { value: "paleo", label: "Paleo" },
  { value: "mediterranean", label: "Mediterráneo" },
  { value: "no_preference", label: "Sin preferencia" },
];

type PatientDrawerProps = {
  open: boolean;
  onClose: () => void;
  onCreated: (patient: Patient) => void;
};

export function PatientDrawer({ open, onClose, onCreated }: PatientDrawerProps) {
  const { addToast } = useToast();
  const [form, setForm] = useState<PatientFormData>(EMPTY_FORM);
  const [saving, setSaving] = useState(false);
  const [showClinical, setShowClinical] = useState(false);
  const [showMetrics, setShowMetrics] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  const update = (field: keyof PatientFormData, value: string) => {
    setForm((prev) => ({ ...prev, [field]: value }));
    if (errors[field]) setErrors((prev) => ({ ...prev, [field]: "" }));
  };

  const validate = (): boolean => {
    const e: Record<string, string> = {};
    if (!form.first_name.trim()) e.first_name = "El nombre es obligatorio";
    if (!form.last_name.trim()) e.last_name = "El apellido es obligatorio";
    setErrors(e);
    return Object.keys(e).length === 0;
  };

  const handleSave = async () => {
    if (!validate()) return;
    setSaving(true);
    try {
      const patient = await createPatient({
        first_name: form.first_name.trim(),
        last_name: form.last_name.trim(),
        birth_date: form.birth_date || undefined,
        sex: form.sex || undefined,
        country: form.country || undefined,
        city: form.city || undefined,
        whatsapp: form.whatsapp || undefined,
        email: form.email || undefined,
      });
      // Note: profile and metrics creation via existing APIs
      // Will be added in Task 3.3 when patient detail API calls are integrated
      addToast("Paciente creado correctamente", "success");
      onCreated(patient);
      setForm(EMPTY_FORM);
      setShowClinical(false);
      setShowMetrics(false);
      onClose();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Error al crear paciente";
      addToast(msg, "error");
    } finally {
      setSaving(false);
    }
  };

  const handleClose = () => {
    if (saving) return;
    setForm(EMPTY_FORM);
    setErrors({});
    setShowClinical(false);
    setShowMetrics(false);
    onClose();
  };

  const inputClass =
    "w-full px-3.5 py-2.5 text-sm border border-slate-200 rounded-xl bg-white text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-colors";
  const labelClass = "block text-sm font-medium text-slate-700 mb-1.5";
  const errorClass = "text-xs text-red-500 mt-1";

  return (
    <AnimatePresence>
      {open && (
        <>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/20 backdrop-blur-sm z-50"
            onClick={handleClose}
          />
          <motion.div
            initial={{ x: "100%" }}
            animate={{ x: 0 }}
            exit={{ x: "100%" }}
            transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
            className="fixed right-0 top-0 bottom-0 w-full md:w-[480px] max-w-full bg-white shadow-xl z-50 flex flex-col"
          >
            {/* Header */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100 shrink-0">
              <h2 className="text-lg font-semibold text-slate-800">Nuevo Paciente</h2>
              <button
                onClick={handleClose}
                className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100"
                disabled={saving}
                aria-label="Cerrar"
              >
                <X size={20} />
              </button>
            </div>

            {/* Body */}
            <div className="flex-1 overflow-y-auto p-6 space-y-6">
              {/* Datos personales */}
              <div className="space-y-4">
                <h3 className="text-sm font-semibold text-slate-800">Datos personales</h3>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className={labelClass}>Nombre *</label>
                    <input
                      className={inputClass}
                      value={form.first_name}
                      onChange={(e) => update("first_name", e.target.value)}
                      placeholder="María"
                    />
                    {errors.first_name && <p className={errorClass}>{errors.first_name}</p>}
                  </div>
                  <div>
                    <label className={labelClass}>Apellido *</label>
                    <input
                      className={inputClass}
                      value={form.last_name}
                      onChange={(e) => update("last_name", e.target.value)}
                      placeholder="García"
                    />
                    {errors.last_name && <p className={errorClass}>{errors.last_name}</p>}
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className={labelClass}>Fecha de nacimiento</label>
                    <input
                      type="date"
                      className={inputClass}
                      value={form.birth_date}
                      onChange={(e) => update("birth_date", e.target.value)}
                    />
                  </div>
                  <div>
                    <label className={labelClass}>Sexo</label>
                    <select
                      className={inputClass}
                      value={form.sex}
                      onChange={(e) => update("sex", e.target.value)}
                    >
                      <option value="">No especificar</option>
                      <option value="female">Femenino</option>
                      <option value="male">Masculino</option>
                    </select>
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className={labelClass}>País</label>
                    <input
                      className={inputClass}
                      value={form.country}
                      onChange={(e) => update("country", e.target.value)}
                      placeholder="Venezuela"
                    />
                  </div>
                  <div>
                    <label className={labelClass}>Ciudad</label>
                    <input
                      className={inputClass}
                      value={form.city}
                      onChange={(e) => update("city", e.target.value)}
                      placeholder="Caracas"
                    />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className={labelClass}>WhatsApp</label>
                    <input
                      className={inputClass}
                      value={form.whatsapp}
                      onChange={(e) => update("whatsapp", e.target.value)}
                      placeholder="+58 412 555 1234"
                    />
                  </div>
                  <div>
                    <label className={labelClass}>Email</label>
                    <input
                      type="email"
                      className={inputClass}
                      value={form.email}
                      onChange={(e) => update("email", e.target.value)}
                      placeholder="maria@email.com"
                    />
                  </div>
                </div>
              </div>

              {/* Perfil clínico — colapsable */}
              <div>
                <button
                  onClick={() => setShowClinical(!showClinical)}
                  className="flex items-center justify-between w-full py-2 text-sm font-semibold text-slate-800 hover:text-slate-600"
                >
                  <span>Perfil clínico (opcional)</span>
                  {showClinical ? <CaretUp size={16} /> : <CaretDown size={16} />}
                </button>
                <AnimatePresence>
                  {showClinical && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: "auto", opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      transition={{ duration: 0.2 }}
                      className="overflow-hidden"
                    >
                      <div className="space-y-3 pt-3">
                        <div>
                          <label className={labelClass}>Objetivo</label>
                          <select
                            className={inputClass}
                            value={form.objective}
                            onChange={(e) => update("objective", e.target.value)}
                          >
                            {OBJECTIVES.map((o) => (
                              <option key={o.value} value={o.value}>
                                {o.label}
                              </option>
                            ))}
                          </select>
                        </div>
                        <div>
                          <label className={labelClass}>Enfermedades</label>
                          <textarea
                            className={inputClass}
                            rows={2}
                            value={form.diseases}
                            onChange={(e) => update("diseases", e.target.value)}
                            placeholder="Ej: Diabetes tipo 2, Hipotiroidismo..."
                          />
                        </div>
                        <div>
                          <label className={labelClass}>Medicamentos</label>
                          <textarea
                            className={inputClass}
                            rows={2}
                            value={form.medications}
                            onChange={(e) => update("medications", e.target.value)}
                            placeholder="Ej: Metformina 850mg, Levotiroxina 50mcg..."
                          />
                        </div>
                        <div>
                          <label className={labelClass}>Alergias alimentarias</label>
                          <textarea
                            className={inputClass}
                            rows={2}
                            value={form.food_allergies}
                            onChange={(e) => update("food_allergies", e.target.value)}
                            placeholder="Ej: Lácteos, Maní, Mariscos..."
                          />
                        </div>
                        <div>
                          <label className={labelClass}>Alimentos a evitar</label>
                          <textarea
                            className={inputClass}
                            rows={2}
                            value={form.foods_avoided}
                            onChange={(e) => update("foods_avoided", e.target.value)}
                            placeholder="Ej: Frituras, Azúcar refinada..."
                          />
                        </div>
                        <div>
                          <label className={labelClass}>Estilo de alimentación</label>
                          <select
                            className={inputClass}
                            value={form.dietary_style}
                            onChange={(e) => update("dietary_style", e.target.value)}
                          >
                            {DIETARY_STYLES.map((d) => (
                              <option key={d.value} value={d.value}>
                                {d.label}
                              </option>
                            ))}
                          </select>
                        </div>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>

              {/* Métricas iniciales — colapsable */}
              <div>
                <button
                  onClick={() => setShowMetrics(!showMetrics)}
                  className="flex items-center justify-between w-full py-2 text-sm font-semibold text-slate-800 hover:text-slate-600"
                >
                  <span>Métricas iniciales (opcional)</span>
                  {showMetrics ? <CaretUp size={16} /> : <CaretDown size={16} />}
                </button>
                <AnimatePresence>
                  {showMetrics && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: "auto", opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      transition={{ duration: 0.2 }}
                      className="overflow-hidden"
                    >
                      <div className="grid grid-cols-2 gap-3 pt-3">
                        <div>
                          <label className={labelClass}>Peso (kg)</label>
                          <input
                            type="number"
                            className={inputClass}
                            value={form.weight_kg}
                            onChange={(e) => update("weight_kg", e.target.value)}
                            placeholder="65.0"
                            step="0.1"
                            min="20"
                            max="300"
                          />
                        </div>
                        <div>
                          <label className={labelClass}>Altura (cm)</label>
                          <input
                            type="number"
                            className={inputClass}
                            value={form.height_cm}
                            onChange={(e) => update("height_cm", e.target.value)}
                            placeholder="162"
                            step="0.1"
                            min="50"
                            max="250"
                          />
                        </div>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            </div>

            {/* Footer */}
            <div className="px-6 py-4 border-t border-slate-100 shrink-0">
              <button
                onClick={handleSave}
                disabled={saving}
                className="w-full py-3 bg-emerald-600 text-white rounded-full text-sm font-semibold hover:bg-emerald-700 active:scale-[0.98] transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                {saving ? (
                  <>
                    <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    Guardando...
                  </>
                ) : (
                  "Guardar paciente"
                )}
              </button>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/patients/PatientDrawer.tsx
git commit -m "feat: add PatientDrawer with full form, collapsible clinical profile and metrics"
```

---

### Task 3.3: Refactor Patients.tsx con nuevos componentes

**Files:** Modify: `frontend/src/pages/Patients.tsx`

- [ ] **Step 1: Reescribir Patients.tsx**

Leer `frontend/src/pages/Patients.tsx` actual para entender la paginación y API calls existentes. Luego reescribir usando `PatientRow`, `PatientDrawer`, `Avatar`, `Badge`, `EmptyState`, `Skeleton`, `Toast`, iconos Phosphor, y búsqueda predictiva.

Los cambios clave:
- Búsqueda debounced con `usePatientSearch`
- Lista usa `PatientRow` con avatares, estados legibles, menú contextual
- Botón "+ Nuevo Paciente" abre `PatientDrawer`
- Filtros: Todos, Con dieta activa, Perfil pendiente, Nuevos este mes
- Loading: `SkeletonRow` x5
- Empty: `EmptyState` con icono `Users` + "Aún no hay pacientes" + botón crear
- Error: mensaje inline + botón reintentar

(Ver implementación completa en Patients.tsx reescrito)

- [ ] **Step 2: Commit**

```bash
git add frontend/src/pages/Patients.tsx
git commit -m "feat: redesign Patients with PatientRow, PatientDrawer, human-readable states, and contextual menus"
```

---

### Task 3.4: Refactor PatientDetail — sin tabs, vista única

**Files:** Modify: `frontend/src/pages/PatientDetail.tsx`
Create: `frontend/src/components/patients/WeightSparkline.tsx`, `frontend/src/components/patients/MetricsModal.tsx`

- [ ] **Step 1: Crear WeightSparkline.tsx**

Sparkline simple SVG generado con puntos de peso vs tiempo.

```tsx
// frontend/src/components/patients/WeightSparkline.tsx
import type { PatientMetric } from "../../types";

type WeightSparklineProps = {
  metrics: PatientMetric[];
};

export function WeightSparkline({ metrics }: WeightSparklineProps) {
  const weightData = metrics
    .filter((m) => m.weight_kg != null)
    .slice(0, 20)
    .reverse();
  if (weightData.length < 2) return null;

  const min = Math.min(...weightData.map((d) => d.weight_kg!));
  const max = Math.max(...weightData.map((d) => d.weight_kg!));
  const range = max - min || 1;
  const w = 200;
  const h = 48;
  const pad = 4;
  const points = weightData
    .map((d, i) => {
      const x = pad + (i / (weightData.length - 1)) * (w - 2 * pad);
      const y = pad + ((max - d.weight_kg!) / range) * (h - 2 * pad);
      return `${x},${y}`;
    })
    .join(" ");

  return (
    <svg viewBox={`0 0 ${w} ${h}`} className="w-full h-12" aria-label="Tendencia de peso">
      <polyline
        points={points}
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        className="text-emerald-500"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}
```

- [ ] **Step 2: Crear MetricsModal.tsx**

Modal pequeño para registrar peso + altura.

```tsx
// frontend/src/components/patients/MetricsModal.tsx
import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X } from "@phosphor-icons/react";
import { addMetric } from "../../services/api";
import { useToast } from "../../context/ToastContext";

type MetricsModalProps = {
  open: boolean;
  onClose: () => void;
  patientId: number;
  onSaved: () => void;
};

export function MetricsModal({ open, onClose, patientId, onSaved }: MetricsModalProps) {
  const { addToast } = useToast();
  const [weight, setWeight] = useState("");
  const [height, setHeight] = useState("");
  const [saving, setSaving] = useState(false);

  const handleSave = async () => {
    if (!weight && !height) return;
    setSaving(true);
    try {
      await addMetric(patientId, {
        weight_kg: weight ? parseFloat(weight) : undefined,
        height_cm: height ? parseFloat(height) : undefined,
        source: "admin",
      });
      addToast("Métricas registradas", "success");
      setWeight("");
      setHeight("");
      onSaved();
      onClose();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Error al guardar métricas";
      addToast(msg, "error");
    } finally {
      setSaving(false);
    }
  };

  const inputClass =
    "w-full px-3.5 py-2.5 text-sm border border-slate-200 rounded-xl bg-white text-slate-800 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500";

  return (
    <AnimatePresence>
      {open && (
        <>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/20 backdrop-blur-sm z-50"
            onClick={onClose}
          />
          <motion.div
            initial={{ opacity: 0, y: 16, scale: 0.96 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 16, scale: 0.96 }}
            className="fixed inset-x-4 top-[20%] max-w-sm mx-auto bg-white rounded-2xl shadow-xl z-50 p-6"
          >
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-semibold text-slate-800">Registrar métricas</h3>
              <button onClick={onClose} className="p-1 rounded-lg text-slate-400 hover:bg-slate-100">
                <X size={18} />
              </button>
            </div>
            <div className="space-y-3">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1.5">Peso (kg)</label>
                <input
                  type="number"
                  className={inputClass}
                  value={weight}
                  onChange={(e) => setWeight(e.target.value)}
                  placeholder="65.0"
                  step="0.1"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1.5">Altura (cm)</label>
                <input
                  type="number"
                  className={inputClass}
                  value={height}
                  onChange={(e) => setHeight(e.target.value)}
                  placeholder="162"
                  step="0.1"
                />
              </div>
            </div>
            <button
              onClick={handleSave}
              disabled={saving || (!weight && !height)}
              className="w-full mt-4 py-2.5 bg-emerald-600 text-white rounded-full text-sm font-semibold hover:bg-emerald-700 active:scale-[0.98] transition-all disabled:opacity-50"
            >
              {saving ? "Guardando..." : "Guardar"}
            </button>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
```

- [ ] **Step 3: Reescribir PatientDetail.tsx**

Leer `frontend/src/pages/PatientDetail.tsx` actual. Reescribir con:
- Vista única scrollable (sin tabs)
- Cabecera con avatar grande, nombre, edad, ciudad, email, whatsapp
- Sección Resumen con peso, altura, IMC, sparkline, dieta activa
- Sección Datos Clínicos (grid 2 cols, labels legibles)
- Sección Historial de Métricas con sparkline + tabla + botón "+ Registrar"
- Sección Dietas anteriores
- Botones de acción: "Nueva Dieta", "Enviar Formulario", "Editar Datos", "Registrar Métricas"
- Estados: loading (skeleton cards), error, empty (sin métricas, sin dietas)

- [ ] **Step 4: Commit**

```bash
git add frontend/src/pages/PatientDetail.tsx frontend/src/components/patients/WeightSparkline.tsx frontend/src/components/patients/MetricsModal.tsx
git commit -m "feat: redesign PatientDetail with single scrollable view, sparkline, metrics modal"
```

---

## Fase 4: Dietas

### Task 4.1: Refactor Diets.tsx — sin IDs, badges legibles

**Files:** Modify: `frontend/src/pages/Diets.tsx`

- [ ] **Step 1: Reescribir Diets.tsx**

Leer `frontend/src/pages/Diets.tsx` actual. Cambios:
- Reemplazar columna ID por avatar + nombre de paciente
- Columna Plan: tipo de dieta + calorías (extraídos de `structured_plan_json`)
- Columna Estado: `Badge` con texto legible
- Columna Generada: fecha relativa ("Hace 3 días", "Hoy")
- Filtro por nombre de paciente, no por ID
- Búsqueda usa `usePatientSearch`
- Loading: skeleton rows
- Empty: "Aún no hay dietas" + botón "Crear primera dieta"
- Preparar checkboxes para batch futuro (ocultos tras feature flag)

- [ ] **Step 2: Commit**

```bash
git add frontend/src/pages/Diets.tsx
git commit -m "feat: redesign Diets with patient names, human-readable status badges, no IDs"
```

---

### Task 4.2: Mejorar DietWizard — búsqueda por nombre, bloqueo perfil

**Files:** Modify: `frontend/src/pages/DietWizard.tsx`, `frontend/src/components/wizard/PatientSearchInput.tsx`

- [ ] **Step 1: Mejorar PatientSearchInput.tsx**

Cambiar `PatientSearchInput` para mostrar nombre completo + ciudad, no ID. Agregar indicador visual de perfil completo/incompleto.

```tsx
// Modificación en PatientSearchInput.tsx
// En el dropdown de resultados, reemplazar:
// Antes: "María García (#42)"
// Después: mostrar Avatar + "María García — Caracas" + badge "Perfil completo ✓"
```

- [ ] **Step 2: Mejorar DietWizard.tsx paso 1 (paciente)**

Agregar bloqueo si el perfil está incompleto:
- Al seleccionar un paciente, verificar `getPatientSummary(patientId)`
- Si `profile_flags.is_profile_complete === false`, mostrar advertencia:
  "Este paciente necesita completar su perfil antes de generar una dieta. ¿Quieres enviarle un formulario de ingesta?"
- Botón "Enviar formulario" + botón "Seleccionar otro paciente"
- Si el perfil está completo, permitir continuar normalmente

- [ ] **Step 3: Agregar estructura para batch futuro en el wizard**

El reducer `WizardState` ya tiene `patientId: number | null`. Agregar campo `patientIds: number[]` (usado cuando se active batch). El paso de selección ya está listo para recibir múltiples pacientes.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/pages/DietWizard.tsx frontend/src/components/wizard/PatientSearchInput.tsx frontend/src/types/index.ts
git commit -m "feat: improve DietWizard with patient name search, profile completeness check, batch-ready structure"
```

---

## Fase 5: Compartir

### Task 5.1: ShareModal — Modal de compartir rediseñado

**Files:** Create: `frontend/src/components/sharing/ShareModal.tsx`
Modify: `frontend/src/components/ShareButtons.tsx`

- [ ] **Step 1: Crear ShareModal.tsx**

Modal que unifica la creación de link + compartir:
- Seleccionar expiración (1, 3, 7, 14, 30 días)
- Botón "Crear formulario" → llama API `createIntakeLink`
- Link generado con botón copiar
- Botones WhatsApp y Email con mensajes pre-compuestos
- Explica al médico qué podrá hacer el paciente

- [ ] **Step 2: Integrar ShareModal en puntos de acceso**

Agregar llamado a `ShareModal` desde:
- `PatientRow` (menú contextual "Enviar formulario")
- `PatientDetail` (botón "Enviar Formulario")
- `Formularios` page (botón "+ Nuevo formulario")

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/sharing/ShareModal.tsx frontend/src/components/ShareButtons.tsx
git commit -m "feat: add ShareModal with link creation, copy, and WhatsApp/Email sharing"
```

---

### Task 5.2: Renombrar /intake-links → /formularios

**Files:** Modify: `frontend/src/pages/IntakeLinks.tsx`

- [ ] **Step 1: Reescribir IntakeLinks.tsx como "Formularios"**

- Título cambia a "Formularios de ingesta"
- Lista de links: paciente (avatar + nombre), estado (badge: Activo, Usado, Revocado, Expirado), creado, expira, acciones (Copiar link, Revocar)
- Botón "+ Nuevo formulario" abre `ShareModal`
- Loading/empty/error states
- Toda la terminología: "formulario" en vez de "intake link"

- [ ] **Step 2: Commit**

```bash
git add frontend/src/pages/IntakeLinks.tsx frontend/src/App.tsx
git commit -m "feat: rebrand intake-links to formularios with redesigned UI and ShareModal integration"
```

---

## Fase 6: Pulido

### Task 6.1: Revisar todos los estados (loading, empty, error)

**Files:** Todas las páginas modificadas

- [ ] **Step 1: Verificar cada página tenga los 3 estados**

Revisar: Dashboard, Patients, PatientDetail, Diets, DietWizard, DietDetail, Formularios, AdminUsers.

Cada página debe tener:
- **Loading:** Skeleton que imita el layout real
- **Empty:** EmptyState con icono + texto + acción
- **Error:** Mensaje inline + botón Reintentar

- [ ] **Step 2: Commit**

```bash
git add frontend/src/pages/
git commit -m "fix: ensure loading, empty, and error states on all pages"
```

---

### Task 6.2: Verificar responsive y PWA

- [ ] **Step 1: Testear en resoluciones 375px, 768px, 1024px, 1440px**

Verificar:
- Sidebar se convierte en drawer en mobile
- Tablas tienen scroll horizontal o se apilan
- Formularios usan inputs nativos (date, select) para mobile
- Touch targets ≥ 44px
- No hay scroll horizontal indeseado
- `h-screen` reemplazado por `min-h-[100dvh]`

- [ ] **Step 2: Probar PWA**

```bash
cd frontend && npm run build && npm run preview
```

- Verificar que el service worker se registra
- Comportamiento offline: al menos mostrar UI con datos cacheados
- `theme_color` y `background_color` correctos en el manifest

- [ ] **Step 3: Commit** (si hay fixes)

```bash
git add -A
git commit -m "fix: responsive and PWA polish"
```

---

## Verificación Final

- [ ] `cd frontend && npm run build` — sin errores
- [ ] `cd frontend && npm run typecheck` — sin errores de TypeScript
- [ ] `cd frontend && npm run dev` — navegar todas las rutas
- [ ] Dashboard muestra KPIs, actividad, progreso — sin IDs
- [ ] Crear paciente desde drawer — ver en lista con avatar
- [ ] Perfil paciente — vista única, sparkline, sin tabs
- [ ] Nueva dieta individual desde perfil y barra superior
- [ ] Lista dietas — sin IDs, badges en español
- [ ] Enviar formulario desde lista pacientes y perfil
- [ ] Compartir por WhatsApp y Email
- [ ] PWA en móvil — sidebar drawer, navegación, formularios
- [ ] Estados vacíos y error en cada página
- [ ] Responsive 375px, 768px, 1440px

---

## Resumen de Commits (15 total)

1. `chore: add framer-motion and @phosphor-icons/react dependencies`
2. `feat: add Avatar and Badge base components`
3. `feat: add Skeleton, EmptyState, and Toast base components`
4. `feat: redesign AdminLayout with Phosphor icons, top bar, breadcrumbs, and mobile drawer`
5. `feat: add /formularios route with redirect from /intake-links`
6. `feat: redesign Dashboard with KPI bento grid, activity timeline, and profile progress`
7. `feat: add PatientRow with avatar, human-readable status, and contextual menu`
8. `feat: add PatientDrawer with full form, collapsible clinical profile and metrics`
9. `feat: redesign Patients with PatientRow, PatientDrawer, human-readable states`
10. `feat: redesign PatientDetail with single scrollable view, sparkline, metrics modal`
11. `feat: redesign Diets with patient names, human-readable status badges, no IDs`
12. `feat: improve DietWizard with patient name search, profile completeness check, batch-ready`
13. `feat: add ShareModal with link creation, copy, and WhatsApp/Email sharing`
14. `feat: rebrand intake-links to formularios with redesigned UI and ShareModal integration`
15. `fix: ensure loading, empty, and error states on all pages` / `fix: responsive and PWA polish`
