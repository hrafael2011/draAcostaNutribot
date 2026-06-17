import { Navigate, useLocation } from "react-router-dom"
import { useAuth } from "../context/AuthContext"

export default function RequireAuth({ children }: { children: React.ReactNode }) {
  const { token, session } = useAuth()
  const location = useLocation()

  if (!token) {
    return <Navigate to="/login" replace state={{ from: location }} />
  }
  if (session?.mustChangePassword) {
    return <Navigate to="/change-password" replace />
  }

  // Block non-admin users from admin routes
  const isAdminRoute = location.pathname.startsWith("/admin")
  if (isAdminRoute && session?.role !== "admin") {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-50 px-4">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-800">403</h1>
          <p className="mt-2 text-gray-500">No tienes permisos para acceder a esta sección.</p>
        </div>
      </div>
    )
  }

  return <>{children}</>
}
