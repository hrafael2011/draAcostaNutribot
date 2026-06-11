import { useState, useEffect, useCallback } from "react"
import { getPatients } from "../services/api"
import type { Patient } from "../types"

export function usePatientSearch() {
  const [query, setQuery] = useState("")
  const [results, setResults] = useState<Patient[]>([])
  const [loading, setLoading] = useState(false)

  const search = useCallback(async (q: string) => {
    if (q.trim().length < 2) {
      setResults([])
      return
    }
    setLoading(true)
    try {
      const data = await getPatients({ search: q.trim(), page: 1, page_size: 10 })
      setResults(data.items)
    } catch {
      setResults([])
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    const timer = setTimeout(() => search(query), 300)
    return () => clearTimeout(timer)
  }, [query, search])

  return { query, setQuery, results, loading }
}
