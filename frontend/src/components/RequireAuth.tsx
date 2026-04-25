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

  return <>{children}</>
}
