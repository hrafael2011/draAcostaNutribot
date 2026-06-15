import { useState, useRef, useEffect } from "react";
import { DayPicker } from "react-day-picker";
import "react-day-picker/style.css";

type DatePickerProps = {
  value: string;
  onChange: (iso: string) => void;
  name?: string;
  placeholder?: string;
  required?: boolean;
};

export default function DatePicker({
  value,
  onChange,
  name,
  placeholder = "DD/MM/AAAA",
  required = false,
}: DatePickerProps) {
  const [open, setOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  const selected = value ? new Date(value + "T00:00:00") : undefined;

  const displayText = value
    ? new Date(value + "T00:00:00").toLocaleDateString("es-ES", {
        day: "2-digit",
        month: "2-digit",
        year: "numeric",
      })
    : "";

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (
        containerRef.current &&
        !containerRef.current.contains(e.target as Node)
      ) {
        setOpen(false);
      }
    }
    if (open) document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, [open]);

  return (
    <div ref={containerRef} className="relative">
      {/* Trigger button */}
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="w-full flex items-center gap-2 px-3.5 py-2.5 text-sm border border-slate-200 rounded-xl bg-white text-slate-800 hover:border-emerald-400 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-colors text-left"
      >
        <span className="text-slate-400 text-base">📅</span>
        <span className={value ? "text-slate-800" : "text-slate-400"}>
          {displayText || placeholder}
        </span>
      </button>

      {/* Hidden input for FormData */}
      {name && (
        <input type="hidden" name={name} value={value} required={required} />
      )}

      {/* Popover calendar */}
      {open && (
        <div className="absolute z-50 mt-1 bg-white border border-slate-200 rounded-2xl shadow-xl p-3">
          <DayPicker
            mode="single"
            selected={selected}
            onSelect={(day) => {
              if (day) {
                const iso = day.toISOString().slice(0, 10);
                onChange(iso);
                setOpen(false);
              }
            }}
            captionLayout="dropdown"
            defaultMonth={selected || new Date(1990, 0)}
            startMonth={new Date(1920, 0)}
            endMonth={new Date()}
            showOutsideDays={false}
            style={
              {
                "--rdp-accent-color": "#10b981",
                "--rdp-accent-background-color": "#d1fae5",
              } as React.CSSProperties
            }
          />
        </div>
      )}
    </div>
  );
}
