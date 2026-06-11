type ProfileProgressProps = {
  total: number;
  complete: number;
};

export function ProfileProgress({ total, complete }: ProfileProgressProps) {
  const incomplete = total - complete;
  const pct = total > 0 ? Math.round((complete / total) * 100) : 0;
  return (
    <div className="space-y-4">
      <div>
        <div className="flex items-baseline justify-between mb-2">
          <span className="text-2xl font-mono font-semibold text-slate-800 tracking-tight tabular-nums">{complete}</span>
          <span className="text-sm text-slate-500">de {total}</span>
        </div>
        <p className="text-sm text-slate-500 mb-3">{pct}% completados</p>
        <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
          <div className="h-full bg-emerald-500 rounded-full transition-all duration-700 ease-[cubic-bezier(0.16,1,0.3,1)]" style={{ width: `${pct}%` }} />
        </div>
      </div>
      <div className="flex gap-4 text-sm">
        <div className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full bg-emerald-500" />
          <span className="text-slate-600">{complete} Completos</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full bg-amber-400" />
          <span className="text-slate-600">{incomplete} Pendientes</span>
        </div>
      </div>
    </div>
  );
}
