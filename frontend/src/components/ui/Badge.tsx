import type { ReactNode } from "react";

type BadgeVariant = "success" | "warning" | "danger" | "neutral" | "info";

interface BadgeProps {
  children: ReactNode;
  variant?: BadgeVariant;
}

const VARIANT_CLASSES: Record<BadgeVariant, string> = {
  success: "bg-emerald-50 text-emerald-700 ring-emerald-600/20",
  warning: "bg-amber-50 text-amber-700 ring-amber-600/20",
  danger: "bg-red-50 text-red-700 ring-red-600/20",
  neutral: "bg-slate-50 text-slate-600 ring-slate-500/20",
  info: "bg-sky-50 text-sky-700 ring-sky-600/20",
};

export function Badge({ children, variant = "neutral" }: BadgeProps) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ring-1 ring-inset ${VARIANT_CLASSES[variant]}`}
    >
      {children}
    </span>
  );
}
