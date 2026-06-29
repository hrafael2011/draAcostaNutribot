import { useEffect, useState } from "react"
import {
  getTelegramBinding,
  resetTelegramBinding,
  startTelegramBinding,
} from "../services/api"
import type { TelegramBindStart, TelegramBindingState } from "../types"

export default function Telegram() {
  const [state, setState] = useState<TelegramBindingState | null>(null)
  const [pending, setPending] = useState<TelegramBindStart | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [msg, setMsg] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  async function refresh() {
    setError(null)
    const s = await getTelegramBinding()
    setState(s)
  }

  useEffect(() => {
    refresh()
      .catch((e) => setError(e instanceof Error ? e.message : "Error"))
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => {
    if (state?.linked) setPending(null)
  }, [state?.linked])

  async function onGenerate() {
    setMsg(null)
    setError(null)
    try {
      const s = await startTelegramBinding()
      setPending(s)
      setMsg("Abre el enlace en el teléfono donde usas Telegram.")
    } catch (e) {
      setError(e instanceof Error ? e.message : "No se pudo iniciar la vinculación")
    }
  }

  async function onReset() {
    if (!confirm("Unlink Telegram from this account?")) return
    setMsg(null)
    setError(null)
    setPending(null)
    try {
      const s = await resetTelegramBinding()
      setState(s)
      setMsg("Telegram desvinculado.")
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error al desvincular")
    }
  }

  async function copy(text: string) {
    try {
      await navigator.clipboard.writeText(text)
      setMsg("Copiado")
    } catch {
      setMsg("Copia manualmente desde el campo de abajo")
    }
  }

  if (loading) {
    return <p>Cargando…</p>
  }

  return (
    <div style={{ maxWidth: 640 }}>
      <h1 style={{ marginTop: 0 }}>Telegram</h1>
      <p style={{ color: "#555" }}>
        Vincula tu Telegram personal para consultar pacientes desde el bot. Configura{" "}
        <code>TELEGRAM_BOT_TOKEN</code> y <code>TELEGRAM_BOT_USERNAME</code> en el servidor,
        establece el webhook en <code>POST /api/telegram/webhook</code>, y opcionalmente{" "}
        <code>TELEGRAM_WEBHOOK_SECRET</code> (debe coincidir con el token secreto de Telegram).
      </p>
      {error && <p style={{ color: "#b00020" }}>{error}</p>}
      {msg && <p style={{ color: "#0a0" }}>{msg}</p>}

      {state && (
        <div
          style={{
            border: "1px solid #ddd",
            borderRadius: 8,
            padding: 16,
            marginBottom: 24,
          }}
        >
          <p style={{ marginTop: 0 }}>
            <strong>Estado:</strong> {state.linked ? "Vinculado" : "No vinculado"}
          </p>
          {state.linked && (
            <>
              <p>
                <strong>ID de usuario:</strong> {state.telegram_user_id ?? "—"}
              </p>
              <p>
                <strong>Nombre de usuario:</strong> @{state.telegram_username ?? "—"}
              </p>
            </>
          )}
          {state.bot_username && (
            <p style={{ fontSize: 14, color: "#666" }}>
              Bot: @{state.bot_username}
            </p>
          )}
        </div>
      )}

      <div style={{ display: "flex", gap: 12, flexWrap: "wrap", alignItems: "center" }}>
        <button type="button" onClick={onGenerate} disabled={!!state?.linked}>
          Generar enlace
        </button>
        <button type="button" onClick={onReset} disabled={!state?.linked}>
          Desvincular Telegram
        </button>
        <button
          type="button"
          onClick={() => {
            setLoading(true)
            refresh()
              .catch((e) => setError(e instanceof Error ? e.message : "Error"))
              .finally(() => setLoading(false))
          }}
        >
          Actualizar estado
        </button>
      </div>

      {pending && (
        <div style={{ marginTop: 24 }}>
          <h2 style={{ fontSize: 16 }}>Enlace de vinculación</h2>
          <p style={{ fontSize: 13, color: "#666" }}>
            Puedes reutilizar el mismo enlace en pruebas; al pulsar «Generate link» se renueva la
            caducidad. Tras «Unlink», el código guardado en base de datos sigue sirviendo. Mientras
            no reinicies o borres la base de datos (p. ej. evita{" "}
            <code>docker compose down -v</code> en desarrollo), el <code>t.me/…?start=…</code>{" "}
            permanece; es independiente de la URL del túnel/ngrok usada solo para el webhook.
          </p>
          <p style={{ fontSize: 14, wordBreak: "break-all" }}>{pending.deep_link}</p>
          <button type="button" onClick={() => copy(pending.deep_link)}>
            Copiar enlace
          </button>
          <p style={{ fontSize: 13, color: "#666" }}>
            Caducidad (técnica): {pending.expires_at}
          </p>
          <p style={{ fontSize: 13, color: "#666" }}>
            Después de vincular, prueba <code>/ayuda</code>, <code>/pacientes</code>, o{" "}
            <code>/ficha NOMBRE</code> en el bot.
          </p>
        </div>
      )}
    </div>
  )
}
