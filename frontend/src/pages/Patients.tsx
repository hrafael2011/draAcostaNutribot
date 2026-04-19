import { FormEvent, useCallback, useEffect, useState } from "react"
import { Link } from "react-router-dom"
import { createPatient, getPatients } from "../services/api"
import type { PaginatedPatients, Patient } from "../types"

export default function Patients() {
  const [data, setData] = useState<PaginatedPatients | null>(null)
  const [search, setSearch] = useState("")
  const [page, setPage] = useState(1)
  const [error, setError] = useState<string | null>(null)
  const [creating, setCreating] = useState(false)
  const [firstName, setFirstName] = useState("")
  const [lastName, setLastName] = useState("")

  const load = useCallback(() => {
    setError(null)
    getPatients({ search: search || undefined, page, page_size: 20 })
      .then(setData)
      .catch((e) => setError(e instanceof Error ? e.message : "Error"))
  }, [page, search])

  useEffect(() => {
    load()
  }, [load])

  async function onSearch(e: FormEvent) {
    e.preventDefault()
    setPage(1)
    setError(null)
    try {
      const d = await getPatients({
        search: search || undefined,
        page: 1,
        page_size: 20,
      })
      setData(d)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error")
    }
  }

  async function onCreate(e: FormEvent) {
    e.preventDefault()
    setError(null)
    try {
      await createPatient({ first_name: firstName, last_name: lastName })
      setFirstName("")
      setLastName("")
      setCreating(false)
      setPage(1)
      load()
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error")
    }
  }

  return (
    <div>
      <h1 style={{ marginTop: 0 }}>Patients</h1>
      <form onSubmit={onSearch} style={{ display: "flex", gap: 8, marginBottom: 16, flexWrap: "wrap" }}>
        <input
          placeholder="Search name"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          style={{ padding: 8, minWidth: 200 }}
        />
        <button type="submit">Search</button>
        <button
          type="button"
          onClick={() => setCreating((c) => !c)}
        >
          {creating ? "Cancel" : "New patient"}
        </button>
      </form>

      {creating && (
        <form
          onSubmit={onCreate}
          style={{
            border: "1px solid #ddd",
            padding: 16,
            borderRadius: 8,
            marginBottom: 24,
            maxWidth: 400,
          }}
        >
          <h2 style={{ fontSize: 16, marginTop: 0 }}>New patient</h2>
          <label style={{ display: "block", fontSize: 13 }}>First name</label>
          <input
            required
            value={firstName}
            onChange={(e) => setFirstName(e.target.value)}
            style={{ width: "100%", padding: 8, marginBottom: 8, boxSizing: "border-box" }}
          />
          <label style={{ display: "block", fontSize: 13 }}>Last name</label>
          <input
            required
            value={lastName}
            onChange={(e) => setLastName(e.target.value)}
            style={{ width: "100%", padding: 8, marginBottom: 8, boxSizing: "border-box" }}
          />
          <button type="submit">Create</button>
        </form>
      )}

      {error && <p style={{ color: "#b00020" }}>{error}</p>}

      {!data ? (
        <p>Loading…</p>
      ) : (
        <>
          <table style={{ borderCollapse: "collapse", width: "100%", maxWidth: 900 }}>
            <thead>
              <tr style={{ textAlign: "left", borderBottom: "1px solid #ccc" }}>
                <th style={{ padding: 8 }}>Name</th>
                <th style={{ padding: 8 }}>City</th>
                <th style={{ padding: 8 }}>Source</th>
                <th style={{ padding: 8 }}>Status</th>
              </tr>
            </thead>
            <tbody>
              {data.items.map((p: Patient) => (
                <tr key={p.id} style={{ borderBottom: "1px solid #eee" }}>
                  <td style={{ padding: 8 }}>
                    <Link to={`/patients/${p.id}`}>
                      {p.first_name} {p.last_name}
                    </Link>
                  </td>
                  <td style={{ padding: 8 }}>{p.city || "—"}</td>
                  <td style={{ padding: 8 }}>{p.source}</td>
                  <td style={{ padding: 8 }}>
                    {p.is_archived ? "archived" : p.is_active ? "active" : "inactive"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <div style={{ marginTop: 16, display: "flex", gap: 12, alignItems: "center" }}>
            <button
              type="button"
              disabled={page <= 1}
              onClick={() => setPage((p) => Math.max(1, p - 1))}
            >
              Previous
            </button>
            <span>
              Page {page} · {data.total} total
            </span>
            <button
              type="button"
              disabled={page * data.page_size >= data.total}
              onClick={() => setPage((p) => p + 1)}
            >
              Next
            </button>
          </div>
        </>
      )}
    </div>
  )
}
