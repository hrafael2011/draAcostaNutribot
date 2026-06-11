import { Avatar } from "../ui/Avatar";

interface Activity {
  id?: number;
  action?: string;
  entity_type?: string;
  entity_id?: number;
  patient_name?: string;
  doctor_name?: string;
  created_at?: string;
  [key: string]: unknown;
}

const ACTION_LABELS: Record<string, string> = {
  diet_generated: "Dieta generada para {patient}",
  diet_regenerated: "Dieta regenerada para {patient}",
  diet_approved: "Dieta aprobada para {patient}",
  patient_created: "Paciente {patient} creado",
  patient_updated: "Paciente {patient} actualizado",
  intake_link_created: "Formulario enviado a {patient}",
  intake_submitted: "Formulario completado por {patient}",
  metric_added: "Metricas registradas para {patient}",
  profile_updated: "Perfil actualizado de {patient}",
};

function timeAgo(dateStr: string): string {
  const now = Date.now();
  const then = new Date(dateStr).getTime();
  const diffMin = Math.floor((now - then) / 60000);
  if (diffMin < 1) return "Ahora mismo";
  if (diffMin < 60) return `Hace ${diffMin} min`;
  const diffHrs = Math.floor(diffMin / 60);
  if (diffHrs < 24) return `Hace ${diffHrs} h`;
  const diffDays = Math.floor(diffHrs / 24);
  if (diffDays < 7) return `Hace ${diffDays} dias`;
  return new Date(dateStr).toLocaleDateString("es-VE", { day: "numeric", month: "short" });
}

function describeAction(a: Activity): string {
  const action = a.action ?? "";
  const patient = a.patient_name ?? "paciente";
  const template = ACTION_LABELS[action];
  if (template) return template.replace("{patient}", patient);
  return `${action} — ${patient}`;
}

export function ActivityTimeline({ activities }: { activities: Activity[] }) {
  if (!activities.length) {
    return <div className="text-center py-8 text-sm text-slate-500">No hay actividad reciente</div>;
  }
  return (
    <div className="space-y-1 max-h-[400px] overflow-y-auto">
      {activities.slice(0, 10).map((a) => (
        <div key={a.id ?? `${a.action}-${a.patient_name}-${a.created_at}`} className="flex items-center gap-3 px-2 py-2.5 rounded-xl hover:bg-slate-50 transition-colors">
          <Avatar firstName={a.patient_name ?? "?"} lastName="" size="sm" />
          <div className="flex-1 min-w-0">
            <p className="text-sm text-slate-700 truncate">{describeAction(a)}</p>
          </div>
          <span className="text-xs text-slate-400 shrink-0">
            {a.created_at ? timeAgo(a.created_at) : ""}
          </span>
        </div>
      ))}
    </div>
  );
}
