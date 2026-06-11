import type { Patient } from "../../types"
import { usePatientSearch } from "../../hooks/usePatientSearch"
import { Avatar } from "../ui/Avatar"

type Props = { onSelect: (patient: Patient) => void }

export default function PatientSearchInput({ onSelect }: Props) {
  const { query, setQuery, results, loading } = usePatientSearch()

  return (
    <div className="space-y-3">
      <label className="block text-sm font-medium text-slate-700">
        Buscar paciente por nombre o apellido
      </label>
      <input
        type="text"
        autoFocus
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Ej: María López"
        className="w-full rounded-xl border border-slate-300 px-3 py-2 text-sm focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
      />
      {loading && <p className="text-sm text-slate-400">Buscando...</p>}
      {results.length > 0 && (
        <div className="space-y-1">
          {results.map((p) => (
            <button
              key={p.id}
              type="button"
              onClick={() => onSelect(p)}
              className="w-full rounded-xl border border-slate-200 px-3 py-2 text-left text-sm hover:bg-slate-50 hover:border-slate-300 transition-colors cursor-pointer flex items-center gap-3"
            >
              <Avatar firstName={p.first_name} lastName={p.last_name} size="sm" />
              <div className="flex-1 min-w-0">
                <span className="font-medium text-slate-800">
                  {p.first_name} {p.last_name}
                </span>
                {p.city ? (
                  <span className="ml-2 text-xs text-slate-400">· {p.city}</span>
                ) : (
                  <span className="ml-2 text-xs text-slate-400">Sin perfil</span>
                )}
              </div>
            </button>
          ))}
        </div>
      )}
      {query.length >= 2 && !loading && results.length === 0 && (
        <p className="text-sm text-slate-400">No se encontraron pacientes</p>
      )}
    </div>
  )
}
