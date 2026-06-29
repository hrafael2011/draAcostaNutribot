import { type ChangeEvent } from "react";

type OptionalFieldProps = {
  label: string;
  value: string;
  onChange: (value: string) => void;
  name?: string;
  placeholder?: string;
  naLabel?: string;
  required?: boolean;
  type?: "textarea" | "input";
  rows?: number;
};

const INPUT_CLASS =
  "w-full px-3.5 py-2.5 text-sm border border-slate-200 rounded-xl bg-white text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-colors";

export default function OptionalField({
  label,
  value,
  onChange,
  name,
  placeholder,
  naLabel = "No aplica",
  required = false,
  type = "textarea",
  rows = 2,
}: OptionalFieldProps) {
  const checked = value === "No aplica";

  function handleCheckboxChange(e: ChangeEvent<HTMLInputElement>) {
    onChange(e.target.checked ? "No aplica" : "");
  }

  function handleTextChange(
    e: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>,
  ) {
    onChange(e.target.value);
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-1.5">
        <label className="text-sm font-medium text-slate-700">
          {label}
          {required && <span className="text-red-500 ml-0.5">*</span>}
        </label>
        <label className="flex items-center gap-1.5 cursor-pointer select-none">
          <input
            type="checkbox"
            checked={checked}
            onChange={handleCheckboxChange}
            className="rounded border-slate-300 text-emerald-600 focus:ring-emerald-500/20 w-4 h-4"
          />
          <span
            className={`text-xs font-medium ${checked ? "text-emerald-600" : "text-slate-500"}`}
          >
            {naLabel}
          </span>
        </label>
      </div>

      {type === "textarea" ? (
        <textarea
          name={!checked ? name : undefined}
          value={checked ? "" : value}
          onChange={handleTextChange}
          disabled={checked}
          rows={rows}
          placeholder={checked ? "No aplica" : placeholder}
          className={`${INPUT_CLASS} resize-none ${checked ? "bg-slate-50 text-slate-400 opacity-60 cursor-not-allowed" : ""}`}
          required={required && !checked}
        />
      ) : (
        <input
          type="text"
          name={!checked ? name : undefined}
          value={checked ? "" : value}
          onChange={handleTextChange}
          disabled={checked}
          placeholder={checked ? "No aplica" : placeholder}
          className={`${INPUT_CLASS} ${checked ? "bg-slate-50 text-slate-400 opacity-60 cursor-not-allowed" : ""}`}
          required={required && !checked}
        />
      )}

      {name && checked && (
        <input type="hidden" name={name} value="No aplica" />
      )}
    </div>
  );
}
