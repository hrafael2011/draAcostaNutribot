import { useMemo } from "react";

type AvatarSize = "sm" | "md" | "lg";

interface AvatarProps {
  firstName?: string;
  lastName?: string;
  size?: AvatarSize;
}

const COLOR_VARIANTS = [
  "bg-emerald-100 text-emerald-700",
  "bg-sky-100 text-sky-700",
  "bg-violet-100 text-violet-700",
  "bg-amber-100 text-amber-700",
  "bg-rose-100 text-rose-700",
  "bg-cyan-100 text-cyan-700",
  "bg-indigo-100 text-indigo-700",
  "bg-teal-100 text-teal-700",
] as const;

const SIZE_CLASSES: Record<AvatarSize, string> = {
  sm: "w-8 h-8 text-xs",
  md: "w-10 h-10 text-sm",
  lg: "w-16 h-16 text-xl",
};

function hashName(name: string): number {
  let hash = 0;
  for (let i = 0; i < name.length; i++) {
    hash = name.charCodeAt(i) + ((hash << 5) - hash);
    hash = hash & hash; // Convert to 32-bit integer
  }
  return Math.abs(hash);
}

export function Avatar({ firstName, lastName, size = "md" }: AvatarProps) {
  const initials = useMemo(() => {
    const first = firstName?.charAt(0) ?? "";
    const last = lastName?.charAt(0) ?? "";
    const result = (first + last).toUpperCase();
    return result || "?";
  }, [firstName, lastName]);

  const colorClass = useMemo(() => {
    const fullName = `${firstName ?? ""}${lastName ?? ""}`;
    const index = hashName(fullName) % COLOR_VARIANTS.length;
    return COLOR_VARIANTS[index];
  }, [firstName, lastName]);

  return (
    <span
      aria-hidden="true"
      className={`rounded-full flex items-center justify-center font-semibold shrink-0 ${SIZE_CLASSES[size]} ${colorClass}`}
    >
      {initials}
    </span>
  );
}
