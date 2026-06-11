import type { Patient } from "../../types"
import { usePatientSearch } from "../../hooks/usePatientSearch"

type Props = { onSelect: (patient: Patient) => void }

export default function PatientSearchInput({ onSelect }: Props) {
  const { query, setQuery, results, loading } = usePatientSearch()

  return (
    <div className="space-y-3">
      <label className="block text-sm font-medium text-gray-700">
        Buscar paciente por nombre o apellido
      </label>
      <input
        type="text"
        autoFocus
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Ej: María López"
        className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
      />
      {loading && <p className="text-sm text-gray-400">Buscando...</p>}
      {results.length > 0 && (
        <div className="space-y-1">
          {results.map((p) => (
            <button
              key={p.id}
              type="button"
              onClick={() => onSelect(p)}
              className="w-full rounded-lg border border-gray-200 px-3 py-2 text-left text-sm hover:bg-emerald-50 hover:border-emerald-300 transition-colors"
            >
              {p.first_name} {p.last_name}
              <span className="ml-2 text-xs text-gray-400">#{p.id}</span>
              {p.city && <span className="ml-2 text-xs text-gray-400">· {p.city}</span>}
            </button>
          ))}
        </div>
      )}
      {query.length >= 2 && !loading && results.length === 0 && (
        <p className="text-sm text-gray-400">No se encontraron pacientes</p>
      )}
    </div>
  )
}
