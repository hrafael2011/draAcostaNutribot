import { Link } from "react-router-dom";
import { DotsThree, User, BowlFood, Envelope, Pencil } from "@phosphor-icons/react";
import { useState, useRef, useEffect } from "react";
import { Avatar } from "../ui/Avatar";
import { Badge } from "../ui/Badge";
import type { Patient, PatientSummary } from "../../types";

type PatientRowProps = {
  patient: Patient;
  summary?: PatientSummary | null;
  onShare?: (patient: Patient) => void;
};

function describeStatus(p: Patient, s?: PatientSummary | null): { label: string; variant: "success" | "warning" | "info" | "neutral" } {
  if (p.is_archived) return { label: "Archivado", variant: "neutral" };
  if (!p.is_active) return { label: "Inactivo", variant: "neutral" };
  if (s?.latest_diet) {
    const daysAgo = Math.floor((Date.now() - new Date(s.latest_diet.created_at).getTime()) / 86400000);
    if (daysAgo <= 0) return { label: "Dieta activa hoy", variant: "success" };
    if (daysAgo === 1) return { label: "Dieta activa ayer", variant: "success" };
    return { label: `Dieta activa hace ${daysAgo} días`, variant: "success" };
  }
  if (!s?.profile_flags?.is_profile_complete) return { label: "Perfil incompleto", variant: "warning" };
  return { label: "Sin dieta aún", variant: "info" };
}

export function PatientRow({ patient, summary, onShare }: PatientRowProps) {
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setMenuOpen(false);
      }
    };
    if (menuOpen) {
      document.addEventListener("mousedown", handler);
      return () => document.removeEventListener("mousedown", handler);
    }
  }, [menuOpen]);

  const status = describeStatus(patient, summary);

  return (
    <div className="flex items-center gap-4 px-4 py-3 hover:bg-slate-50 transition-colors group">
      <Avatar firstName={patient.first_name} lastName={patient.last_name} size="md" />
      <div className="flex-1 min-w-0">
        <Link to={`/patients/${patient.id}`} className="text-sm font-medium text-slate-800 hover:text-emerald-600 truncate block">
          {patient.first_name} {patient.last_name}
        </Link>
        <p className="text-xs text-slate-500 truncate">{patient.city ?? "Sin ciudad"}</p>
      </div>
      <Badge variant={status.variant}>{status.label}</Badge>
      {/* Actions menu */}
      <div className="relative" ref={menuRef}>
        <button
          onClick={() => setMenuOpen(!menuOpen)}
          className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100 opacity-0 group-hover:opacity-100 transition-all"
          aria-label="Acciones"
        >
          <DotsThree size={18} weight="bold" />
        </button>
        {menuOpen && (
          <div className="absolute right-0 top-full mt-1 w-52 bg-white rounded-xl shadow-lg border border-slate-200 z-50 py-1">
            <Link to={`/patients/${patient.id}`} className="flex items-center gap-2 px-3 py-2 text-sm text-slate-600 hover:bg-slate-50" onClick={() => setMenuOpen(false)}>
              <User size={16} /> Ver perfil
            </Link>
            <Link to={`/diets/new?patient=${patient.id}`} className="flex items-center gap-2 px-3 py-2 text-sm text-slate-600 hover:bg-slate-50" onClick={() => setMenuOpen(false)}>
              <BowlFood size={16} /> Nueva dieta
            </Link>
            <button onClick={() => { setMenuOpen(false); onShare?.(patient); }} className="flex items-center gap-2 px-3 py-2 text-sm text-slate-600 hover:bg-slate-50 w-full text-left">
              <Envelope size={16} /> Enviar formulario
            </button>
            <Link to={`/patients/${patient.id}`} className="flex items-center gap-2 px-3 py-2 text-sm text-slate-600 hover:bg-slate-50" onClick={() => setMenuOpen(false)}>
              <Pencil size={16} /> Editar datos
            </Link>
          </div>
        )}
      </div>
    </div>
  );
}
