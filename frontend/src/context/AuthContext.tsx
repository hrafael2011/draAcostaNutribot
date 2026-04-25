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
  changePasswordRequest,
  getStoredToken,
  loginRequest,
  setStoredToken,
} from "../services/api"

type AuthSession = {
  role: string
  mustChangePassword: boolean
}

type AuthContextValue = {
  token: string | null
  session: AuthSession | null
  login: (email: string, password: string) => Promise<void>
  changePassword: (currentPassword: string, newPassword: string) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(getStoredToken)
  const [session, setSession] = useState<AuthSession | null>(() =>
    readSessionFromToken(getStoredToken()),
  )

  useEffect(() => {
    setUnauthorizedHandler(() => {
      setStoredToken(null)
      setToken(null)
      setSession(null)
    })
    return () => setUnauthorizedHandler(null)
  }, [])

  const login = useCallback(async (email: string, password: string) => {
    const data = await loginRequest(email, password)
    const nextToken = getStoredToken()
    setToken(nextToken)
    setSession({
      role: data.role || "doctor",
      mustChangePassword: Boolean(data.must_change_password),
    })
  }, [])

  const changePassword = useCallback(
    async (currentPassword: string, newPassword: string) => {
      const data = await changePasswordRequest(currentPassword, newPassword)
      const nextToken = getStoredToken()
      setToken(nextToken)
      setSession({
        role: data.role || "doctor",
        mustChangePassword: Boolean(data.must_change_password),
      })
    },
    [],
  )

  const logout = useCallback(() => {
    setStoredToken(null)
    setToken(null)
    setSession(null)
  }, [])

  const value = useMemo(
    () => ({ token, session, login, changePassword, logout }),
    [token, session, login, changePassword, logout],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

function readSessionFromToken(token: string | null): AuthSession | null {
  if (!token) return null
  try {
    const payload = JSON.parse(decodeBase64Url(token.split(".")[1] || ""))
    return {
      role: typeof payload.role === "string" ? payload.role : "doctor",
      mustChangePassword: Boolean(payload.must_change_password),
    }
  } catch {
    return null
  }
}

function decodeBase64Url(value: string) {
  const base64 = value.replace(/-/g, "+").replace(/_/g, "/")
  const padded = base64.padEnd(base64.length + ((4 - (base64.length % 4)) % 4), "=")
  return atob(padded)
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error("useAuth must be used within AuthProvider")
  return ctx
}
