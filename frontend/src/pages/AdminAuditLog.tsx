import { useCallback, useEffect, useState } from "react"
import { getAuditLogs } from "../services/api"
import type { AuditLogEntry } from "../types"
import { ClipboardText } from "@phosphor-icons/react"

export default function AdminAuditLog() {
  const [logs, setLogs] = useState<AuditLogEntry[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(() => {
    setError(null)
    setLoading(true)
    getAuditLogs()
      .then(setLogs)
      .catch((err) =>
        setError(err instanceof Error ? err.message : "Error al cargar auditoría"),
      )
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => { load() }, [load])

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-800">Auditoría</h1>
        <p className="mt-1 text-sm text-gray-500">
          Historial de acciones administrativas
        </p>
      </div>

      {error && (
        <div className="mb-4 rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700 border border-red-200">
          {error}
        </div>
      )}

      {loading ? (
        <div className="space-y-3">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-14 animate-pulse rounded-lg bg-gray-100" />
          ))}
        </div>
      ) : logs.length === 0 ? (
        <div className="rounded-xl border border-dashed border-gray-300 p-12 text-center">
          <ClipboardText size={48} className="mx-auto mb-3 text-gray-300" />
          <p className="text-gray-500">No hay acciones registradas</p>
        </div>
      ) : (
        <div className="overflow-x-auto rounded-xl border border-gray-200">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200 bg-gray-50 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                <th className="px-4 py-3">Fecha</th>
                <th className="px-4 py-3">Administrador</th>
                <th className="px-4 py-3">Acción</th>
                <th className="px-4 py-3">Usuario afectado</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {logs.map((log) => (
                <tr key={log.id} className="hover:bg-gray-50 transition-colors">
                  <td className="px-4 py-3 text-xs text-gray-400 whitespace-nowrap">
                    {new Date(log.date).toLocaleString("es-ES")}
                  </td>
                  <td className="px-4 py-3 font-medium text-gray-800">
                    {log.admin}
                  </td>
                  <td className="px-4 py-3 text-gray-600 max-w-md">
                    {log.action}
                  </td>
                  <td className="px-4 py-3 text-gray-500">
                    {log.affected_user}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
