import { useEffect } from "react"
import { useRegisterSW } from "virtual:pwa-register/react"

/** Auto-reloads the page when a PWA update is ready, no user prompt. */
export default function PwaAutoReload() {
  const { needRefresh, updateServiceWorker } = useRegisterSW()

  useEffect(() => {
    if (needRefresh) {
      updateServiceWorker(true) // skipWaiting + reload
    }
  }, [needRefresh, updateServiceWorker])

  return null
}
