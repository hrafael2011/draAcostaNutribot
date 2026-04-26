import { useEffect, useState } from "react"
import { Outlet, NavLink, useNavigate } from "react-router-dom"
import { useAuth } from "../context/AuthContext"
import { getDoctorMe } from "../services/api"
import type { DoctorOut } from "../types"

const navItems = [
  { to: "/dashboard", label: "Dashboard" },
  { to: "/patients", label: "Patients" },
  { to: "/intake-links", label: "Intake Links" },
  { to: "/diets", label: "Diets" },
  { to: "/telegram", label: "Telegram" },
]

export default function AdminLayout() {
  const { logout, session } = useAuth()
  const navigate = useNavigate()
  const [me, setMe] = useState<DoctorOut | null>(null)

  useEffect(() => {
    let cancelled = false
    getDoctorMe()
      .then((d) => {
        if (!cancelled) setMe(d as DoctorOut)
      })
      .catch((e) => {
        if (cancelled) return
        if (e instanceof Error && e.message === "UNAUTHORIZED") {
          logout()
          navigate("/login", { replace: true })
          return
        }
        setMe(null)
      })
    return () => {
      cancelled = true
    }
  }, [logout, navigate])

  const visibleNavItems =
    (me?.role || session?.role) === "admin"
      ? [...navItems, { to: "/admin/users", label: "Usuarios" }]
      : navItems

  return (
    <div style={{ display: "flex", minHeight: "100vh", fontFamily: "system-ui, sans-serif" }}>
      <aside style={{ width: 240, padding: 24, borderRight: "1px solid #ddd" }}>
        <div style={{ fontWeight: 700, marginBottom: 16 }}>Diet Admin</div>
        <nav style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          {visibleNavItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              style={({ isActive }) => ({
                textDecoration: "none",
                color: isActive ? "#111" : "#555",
                fontWeight: isActive ? 700 : 400,
              })}
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
      </aside>
      <main style={{ flex: 1, padding: 32, display: "flex", flexDirection: "column" }}>
        <header
          style={{
            display: "flex",
            justifyContent: "flex-end",
            alignItems: "center",
            gap: 16,
            marginBottom: 16,
          }}
        >
          <span style={{ color: "#555", fontSize: 14 }}>
            {me ? `${me.full_name} · ${me.email}` : ""}
          </span>
          <button
            type="button"
            onClick={() => {
              logout()
              navigate("/login", { replace: true })
            }}
            style={{ padding: "6px 12px" }}
          >
            Log out
          </button>
        </header>
        <Outlet />
      </main>
    </div>
  )
}
