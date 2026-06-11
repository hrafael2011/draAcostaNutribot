import type { ReactNode } from "react";

type KpiCardProps = {
  label: string;
  value: string | number;
  trend?: { direction: "up" | "down"; value: string };
  icon: ReactNode;
};

export function KpiCard({ label, value, trend, icon }: KpiCardProps) {
  return (
    <div className="bg-white rounded-2xl p-6 shadow-[0_20px_40px_-15px_rgba(0,0,0,0.05)]">
      <div className="flex items-center justify-between mb-4">
        <span className="text-sm font-medium text-slate-500">{label}</span>
        <span className="text-slate-300">{icon}</span>
      </div>
      <p className="text-4xl font-mono tracking-tight font-semibold text-slate-800 tabular-nums">
        {value}
      </p>
      {trend && (
        <p className={`mt-2 text-sm font-medium ${trend.direction === "up" ? "text-emerald-600" : "text-red-500"}`}>
          {trend.direction === "up" ? "↑" : "↓"} {trend.value}
        </p>
      )}
    </div>
  );
}
