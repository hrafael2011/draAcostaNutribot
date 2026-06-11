import { Avatar } from "../ui/Avatar";

type Activity = Record<string, unknown> & {
  action?: string;
  entity_type?: string;
  patient_name?: string;
  created_at?: string;
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
  if (diffDays < 7) return `Hace ${diffDays} días`;
  return new Date(dateStr).toLocaleDateString("es-VE", { day: "numeric", month: "short" });
}

function describeAction(a: Activity): string {
  const action = (a.action as string) ?? "";
  const patient = (a.patient_name as string) ?? "paciente";
  if (action.includes("diet")) return `Dieta generada para ${patient}`;
  if (action.includes("patient_created")) return `Paciente ${patient} creado`;
  if (action.includes("intake")) return `Formulario enviado a ${patient}`;
  if (action.includes("metric")) return `Métricas registradas para ${patient}`;
  if (action.includes("profile")) return `Perfil actualizado de ${patient}`;
  return `${action} — ${patient}`;
}

export function ActivityTimeline({ activities }: { activities: Activity[] }) {
  if (!activities.length) {
    return <div className="text-center py-8 text-sm text-slate-500">No hay actividad reciente</div>;
  }
  return (
    <div className="space-y-1 max-h-[400px] overflow-y-auto">
      {activities.slice(0, 10).map((a, i) => (
        <div key={i} className="flex items-center gap-3 px-2 py-2.5 rounded-xl hover:bg-slate-50 transition-colors">
          <Avatar firstName={(a.patient_name as string) ?? "?"} lastName="" size="sm" />
          <div className="flex-1 min-w-0">
            <p className="text-sm text-slate-700 truncate">{describeAction(a)}</p>
          </div>
          <span className="text-xs text-slate-400 shrink-0">
            {a.created_at ? timeAgo(a.created_at as string) : ""}
          </span>
        </div>
      ))}
    </div>
  );
}
