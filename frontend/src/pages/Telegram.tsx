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
      setMsg("Open the link on the phone where you use Telegram.")
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not start binding")
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
      setMsg("Telegram unlinked.")
    } catch (e) {
      setError(e instanceof Error ? e.message : "Reset failed")
    }
  }

  async function copy(text: string) {
    try {
      await navigator.clipboard.writeText(text)
      setMsg("Copied")
    } catch {
      setMsg("Copy manually from the field below")
    }
  }

  if (loading) {
    return <p>Loading…</p>
  }

  return (
    <div style={{ maxWidth: 640 }}>
      <h1 style={{ marginTop: 0 }}>Telegram</h1>
      <p style={{ color: "#555" }}>
        Link your personal Telegram so you can query patients from the bot. Configure{" "}
        <code>TELEGRAM_BOT_TOKEN</code> and <code>TELEGRAM_BOT_USERNAME</code> on the server,
        set the webhook to <code>POST /api/telegram/webhook</code>, and optionally{" "}
        <code>TELEGRAM_WEBHOOK_SECRET</code> (must match Telegram&apos;s secret token header).
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
            <strong>Status:</strong> {state.linked ? "Linked" : "Not linked"}
          </p>
          {state.linked && (
            <>
              <p>
                <strong>User ID:</strong> {state.telegram_user_id ?? "—"}
              </p>
              <p>
                <strong>Username:</strong> @{state.telegram_username ?? "—"}
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
          Generate link
        </button>
        <button type="button" onClick={onReset} disabled={!state?.linked}>
          Unlink Telegram
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
          Refresh status
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
            Copy link
          </button>
          <p style={{ fontSize: 13, color: "#666" }}>
            Caducidad (técnica): {pending.expires_at}
          </p>
          <p style={{ fontSize: 13, color: "#666" }}>
            After linking, try <code>/ayuda</code>, <code>/pacientes</code>, or{" "}
            <code>/ficha NAME</code> in the bot.
          </p>
        </div>
      )}
    </div>
  )
}
