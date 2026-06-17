import { Navigate, useLocation } from "react-router-dom"
import { useAuth } from "../context/AuthContext"

export default function RequireAuth({ children }: { children: React.ReactNode }) {
  const { token, session } = useAuth()
  const location = useLocation()

  if (!token) {
    const isAdminRoute = location.pathname.startsWith("/admin")
    return <Navigate to={isAdminRoute ? "/admin" : "/login"} replace state={{ from: location }} />
  }
  if (session?.mustChangePassword) {
    return <Navigate to="/change-password" replace />
  }

  const isAdmin = session?.role === "admin" || session?.role === "super_admin"

  // Block non-admin users from admin routes
  const isAdminRoute = location.pathname.startsWith("/admin")
  if (isAdminRoute && !isAdmin) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-50 px-4">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-800">403</h1>
          <p className="mt-2 text-gray-500">No tienes permisos para acceder a esta sección.</p>
        </div>
      </div>
    )
  }

  // Redirect admins away from doctor routes
  if (isAdmin && !isAdminRoute) {
    return <Navigate to="/admin/users" replace />
  }

  return <>{children}</>
}
