import { type CSSProperties, useEffect, useState } from "react"
import { getDashboard } from "../services/api"
import type { DashboardSummary } from "../types"

export default function Dashboard() {
  const [data, setData] = useState<DashboardSummary | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    getDashboard()
      .then((d) => {
        if (!cancelled) setData(d)
      })
      .catch((e) => {
        if (!cancelled) setError(e instanceof Error ? e.message : "Error")
      })
    return () => {
      cancelled = true
    }
  }, [])

  if (error) {
    return <p style={{ color: "#b00020" }}>{error}</p>
  }
  if (!data) {
    return <p>Loading…</p>
  }

  const card: CSSProperties = {
    border: "1px solid #ddd",
    borderRadius: 8,
    padding: 16,
    minWidth: 160,
  }

  return (
    <div>
      <h1 style={{ marginTop: 0 }}>Dashboard</h1>
      <div style={{ display: "flex", flexWrap: "wrap", gap: 16 }}>
        <div style={card}>
          <div style={{ fontSize: 13, color: "#666" }}>Total patients</div>
          <div style={{ fontSize: 28, fontWeight: 700 }}>{data.total_patients}</div>
        </div>
        <div style={card}>
          <div style={{ fontSize: 13, color: "#666" }}>New (30 days)</div>
          <div style={{ fontSize: 28, fontWeight: 700 }}>{data.new_patients_30d}</div>
        </div>
        <div style={card}>
          <div style={{ fontSize: 13, color: "#666" }}>Incomplete profiles</div>
          <div style={{ fontSize: 28, fontWeight: 700 }}>{data.incomplete_profiles}</div>
        </div>
        <div style={card}>
          <div style={{ fontSize: 13, color: "#666" }}>Diets</div>
          <div style={{ fontSize: 28, fontWeight: 700 }}>{data.diets_generated}</div>
        </div>
      </div>
      <h2 style={{ marginTop: 32, fontSize: 18 }}>Latest activity</h2>
      {data.latest_activity.length === 0 ? (
        <p style={{ color: "#666" }}>No audit entries yet.</p>
      ) : (
        <ul style={{ paddingLeft: 18 }}>
          {data.latest_activity.map((row) => (
            <li
              key={String(row.id ?? `${row.action}-${row.created_at}`)}
              style={{ marginBottom: 6, fontSize: 14 }}
            >
              <code>{String(row.action)}</code>
              {row.entity_type != null && (
                <>
                  {" "}
                  · {String(row.entity_type)} #{String(row.entity_id)}
                </>
              )}
              {row.created_at != null && (
                <span style={{ color: "#666" }}> · {String(row.created_at)}</span>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
