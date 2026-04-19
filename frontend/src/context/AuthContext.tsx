import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react"
import { setUnauthorizedHandler } from "../services/authBridge"
import {
  getStoredToken,
  loginRequest,
  setStoredToken,
} from "../services/api"

type AuthContextValue = {
  token: string | null
  login: (email: string, password: string) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(getStoredToken)

  useEffect(() => {
    setUnauthorizedHandler(() => {
      setStoredToken(null)
      setToken(null)
    })
    return () => setUnauthorizedHandler(null)
  }, [])

  const login = useCallback(async (email: string, password: string) => {
    await loginRequest(email, password)
    setToken(getStoredToken())
  }, [])

  const logout = useCallback(() => {
    setStoredToken(null)
    setToken(null)
  }, [])

  const value = useMemo(
    () => ({ token, login, logout }),
    [token, login, logout],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error("useAuth must be used within AuthProvider")
  return ctx
}
