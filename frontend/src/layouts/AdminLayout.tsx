import { useState, useEffect } from "react"
import { Outlet, NavLink, useNavigate } from "react-router-dom"
import { useAuth } from "../context/AuthContext"
import { getDoctorMe } from "../services/api"

type DoctorMe = { full_name: string; email: string; role: string }

export default function AdminLayout() {
  const [doctor, setDoctor] = useState<DoctorMe | null>(null)
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const { logout } = useAuth()
  const navigate = useNavigate()

  useEffect(() => {
    let cancelled = false
    getDoctorMe()
      .then((d) => {
        if (!cancelled)
          setDoctor({ full_name: d.full_name, email: d.email, role: d.role })
      })
      .catch(() => {
        if (cancelled) return
        logout()
        navigate("/login", { replace: true })
      })
    return () => {
      cancelled = true
    }
  }, [logout, navigate])

  const linkClass = ({ isActive }: { isActive: boolean }) =>
    `flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
      isActive
        ? "bg-emerald-100 text-emerald-700"
        : "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
    }`

  const navItems = [
    { to: "/dashboard", label: "Dashboard", icon: "📊" },
    { to: "/patients", label: "Pacientes", icon: "👥" },
    { to: "/diets", label: "Dietas", icon: "🍽️" },
    { to: "/intake-links", label: "Links", icon: "🔗" },
    { to: "/telegram", label: "Telegram", icon: "📱" },
  ]

  if (doctor?.role === "admin") {
    navItems.push({ to: "/admin/users", label: "Usuarios", icon: "⚙️" })
  }

  const SidebarContent = () => (
    <div className="flex h-full flex-col">
      {/* Logo + Doctor info */}
      <div className="flex items-center gap-3 border-b border-gray-200 px-4 py-4">
        <img
          src="/logo-sidebar.webp"
          alt="Logo"
          width={48}
          height={46}
          className="rounded-lg shadow-sm"
        />
        <div className="min-w-0">
          <p className="truncate text-sm font-semibold text-gray-800">
            {doctor?.full_name || "Doctora"}
          </p>
          <p className="truncate text-xs text-gray-500">{doctor?.email}</p>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-1 px-2 py-4">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === "/dashboard"}
            className={linkClass}
            onClick={() => setSidebarOpen(false)}
          >
            <span>{item.icon}</span>
            {item.label}
          </NavLink>
        ))}
      </nav>

      {/* Logout */}
      <div className="border-t border-gray-200 px-2 py-3">
        <button
          type="button"
          onClick={() => {
            logout()
            navigate("/login", { replace: true })
          }}
          className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium text-gray-500 hover:bg-red-50 hover:text-red-600 transition-colors"
        >
          🚪 Cerrar sesion
        </button>
      </div>
    </div>
  )

  return (
    <div className="flex min-h-screen bg-gray-50">
      {/* Desktop sidebar */}
      <aside className="hidden md:flex md:w-60 md:flex-col md:bg-white md:border-r md:border-gray-200 md:fixed md:inset-y-0">
        <SidebarContent />
      </aside>

      {/* Mobile sidebar overlay */}
      {sidebarOpen && (
        <div className="fixed inset-0 z-40 md:hidden">
          <div
            className="fixed inset-0 bg-black/50"
            onClick={() => setSidebarOpen(false)}
          />
          <aside className="fixed inset-y-0 left-0 w-72 bg-white shadow-xl z-50">
            <SidebarContent />
          </aside>
        </div>
      )}

      {/* Main content */}
      <div className="flex flex-1 flex-col md:ml-60">
        {/* Top bar (mobile) */}
        <header className="sticky top-0 z-30 flex items-center gap-3 border-b border-gray-200 bg-white px-4 py-2 md:hidden">
          <button
            type="button"
            onClick={() => setSidebarOpen(true)}
            className="rounded-lg p-1 text-gray-500 hover:bg-gray-100"
            aria-label="Abrir menu"
          >
            <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>
          <img
            src="/logo-mobile.webp"
            alt="Logo"
            width={32}
            height={31}
            className="rounded-md"
          />
          <p className="text-sm font-semibold text-gray-800 truncate">
            {doctor?.full_name || "Nutribot"}
          </p>
        </header>

        {/* Page content */}
        <main className="flex-1 p-4 md:p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
