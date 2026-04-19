import { FormEvent, useEffect, useMemo, useState } from "react"
import { Link } from "react-router-dom"
import {
  createIntakeLink,
  getIntakeLinks,
  getPatients,
  revokeIntakeLink,
} from "../services/api"
import type { IntakeLink, Patient } from "../types"

export default function IntakeLinks() {
  const [links, setLinks] = useState<IntakeLink[]>([])
  const [patients, setPatients] = useState<Patient[]>([])
  const [error, setError] = useState<string | null>(null)
  const [msg, setMsg] = useState<string | null>(null)
  const [patientId, setPatientId] = useState<number | "">("")
  const [expiresDays, setExpiresDays] = useState(7)
  const [maxUses, setMaxUses] = useState(1)

  const patientById = useMemo(() => {
    const m = new Map<number, Patient>()
    patients.forEach((p) => m.set(p.id, p))
    return m
  }, [patients])

  async function refresh() {
    setError(null)
    const [ls, pg] = await Promise.all([
      getIntakeLinks(),
      getPatients({ page: 1, page_size: 200 }),
    ])
    setLinks(ls)
    setPatients(pg.items)
  }

  useEffect(() => {
    refresh().catch((e) => setError(e instanceof Error ? e.message : "Error"))
  }, [])

  function publicUrl(token: string) {
    return `${window.location.origin}/intake/${encodeURIComponent(token)}`
  }

  async function onCreate(e: FormEvent) {
    e.preventDefault()
    if (patientId === "") return
    setMsg(null)
    setError(null)
    try {
      await createIntakeLink({
        patient_id: Number(patientId),
        expires_in_days: expiresDays,
        max_uses: maxUses,
      })
      setMsg("Link created")
      await refresh()
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error")
    }
  }

  async function onRevoke(id: number) {
    if (!confirm("Revoke this link?")) return
    setError(null)
    try {
      await revokeIntakeLink(id)
      await refresh()
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error")
    }
  }

  async function copy(text: string) {
    try {
      await navigator.clipboard.writeText(text)
      setMsg("Copied to clipboard")
    } catch {
      setMsg("Could not copy — copy manually")
    }
  }

  return (
    <div>
      <h1 style={{ marginTop: 0 }}>Intake links</h1>
      <p style={{ color: "#555", maxWidth: 640 }}>
        Share the public URL with the patient. They can complete their intake without logging in.
      </p>

      <form
        onSubmit={onCreate}
        style={{
          border: "1px solid #ddd",
          padding: 16,
          borderRadius: 8,
          marginBottom: 24,
          maxWidth: 480,
        }}
      >
        <h2 style={{ fontSize: 16, marginTop: 0 }}>New link</h2>
        <label style={{ display: "block", fontSize: 13 }}>Patient</label>
        <select
          required
          value={patientId}
          onChange={(e) =>
            setPatientId(e.target.value === "" ? "" : Number(e.target.value))
          }
          style={{ width: "100%", padding: 8, marginBottom: 12 }}
        >
          <option value="">Select…</option>
          {patients.map((p) => (
            <option key={p.id} value={p.id}>
              {p.first_name} {p.last_name} (#{p.id})
            </option>
          ))}
        </select>
        <label style={{ display: "block", fontSize: 13 }}>Expires in (days)</label>
        <input
          type="number"
          min={1}
          value={expiresDays}
          onChange={(e) => setExpiresDays(Number(e.target.value))}
          style={{ width: "100%", padding: 8, marginBottom: 12, boxSizing: "border-box" }}
        />
        <label style={{ display: "block", fontSize: 13 }}>Max uses</label>
        <input
          type="number"
          min={1}
          value={maxUses}
          onChange={(e) => setMaxUses(Number(e.target.value))}
          style={{ width: "100%", padding: 8, marginBottom: 12, boxSizing: "border-box" }}
        />
        <button type="submit">Create link</button>
      </form>

      {error && <p style={{ color: "#b00020" }}>{error}</p>}
      {msg && <p style={{ color: "#0a0" }}>{msg}</p>}

      <table style={{ borderCollapse: "collapse", width: "100%", maxWidth: 960 }}>
        <thead>
          <tr style={{ textAlign: "left", borderBottom: "1px solid #ccc" }}>
            <th style={{ padding: 8 }}>Patient</th>
            <th style={{ padding: 8 }}>Status</th>
            <th style={{ padding: 8 }}>Uses</th>
            <th style={{ padding: 8 }}>Expires</th>
            <th style={{ padding: 8 }}>URL</th>
            <th style={{ padding: 8 }} />
          </tr>
        </thead>
        <tbody>
          {links.map((l) => {
            const p = patientById.get(l.patient_id)
            const name = p ? `${p.first_name} ${p.last_name}` : `#${l.patient_id}`
            const url = publicUrl(l.token)
            return (
              <tr key={l.id} style={{ borderBottom: "1px solid #eee", verticalAlign: "top" }}>
                <td style={{ padding: 8 }}>
                  {p ? <Link to={`/patients/${p.id}`}>{name}</Link> : name}
                </td>
                <td style={{ padding: 8 }}>{l.status}</td>
                <td style={{ padding: 8 }}>
                  {l.use_count} / {l.max_uses}
                </td>
                <td style={{ padding: 8, fontSize: 13 }}>{l.expires_at}</td>
                <td style={{ padding: 8, fontSize: 12, wordBreak: "break-all" }}>
                  <button type="button" onClick={() => copy(url)}>
                    Copy URL
                  </button>
                  <div style={{ marginTop: 4, color: "#666" }}>{url}</div>
                </td>
                <td style={{ padding: 8 }}>
                  <button type="button" onClick={() => onRevoke(l.id)}>
                    Revoke
                  </button>
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
