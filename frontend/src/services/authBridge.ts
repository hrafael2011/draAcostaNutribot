type UnauthorizedHandler = () => void

let handler: UnauthorizedHandler | null = null

/** Registered by `AuthProvider` so `authFetch` can clear in-memory session on 401. */
export function setUnauthorizedHandler(next: UnauthorizedHandler | null) {
  handler = next
}

export function notifyUnauthorized() {
  handler?.()
}
