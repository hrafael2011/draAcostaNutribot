import { useState, type ChangeEvent } from "react";

export const IN_TO_CM = 2.54;

type HeightInputProps = {
  valueCm: string;
  onChangeCm: (cm: string) => void;
  name?: string;
  required?: boolean;
  placeholder?: string;
};

const INPUT_CLASS =
  "flex-1 px-3.5 py-2.5 text-sm border border-slate-200 rounded-xl bg-white text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-colors";

export default function HeightInput({
  valueCm,
  onChangeCm,
  name,
  required = false,
  placeholder = "0",
}: HeightInputProps) {
  const [unit, setUnit] = useState<"cm" | "ftin">("cm");
  const cm = parseFloat(valueCm);

  const displayCm = unit === "cm" && valueCm ? valueCm : "";
  const totalInches = !isNaN(cm) ? cm / IN_TO_CM : 0;
  const displayFt =
    unit === "ftin" && valueCm ? Math.floor(totalInches / 12).toString() : "";
  const displayIn =
    unit === "ftin" && valueCm
      ? Math.round(totalInches % 12).toString()
      : "";

  function handleCmChange(e: ChangeEvent<HTMLInputElement>) {
    const raw = e.target.value;
    if (raw === "" || raw === "-") {
      onChangeCm("");
      return;
    }
    const num = parseFloat(raw);
    if (isNaN(num)) return;
    onChangeCm(String(num));
  }

  function handleFtInChange(ftStr: string, inStr: string) {
    const ft = parseFloat(ftStr) || 0;
    const inch = parseFloat(inStr) || 0;
    if (ft === 0 && inStr === "") {
      onChangeCm("");
      return;
    }
    const cmValue = (ft * 12 + inch) * IN_TO_CM;
    onChangeCm(String(cmValue));
  }

  function handleUnitChange(e: ChangeEvent<HTMLSelectElement>) {
    setUnit(e.target.value as "cm" | "ftin");
  }

  return (
    <div className="flex gap-2 items-center">
      <select
        value={unit}
        onChange={handleUnitChange}
        className="px-2 py-2.5 text-sm border border-slate-200 rounded-xl bg-white text-slate-700 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-colors shrink-0"
      >
        <option value="cm">cm</option>
        <option value="ftin">ft/in</option>
      </select>
      {unit === "cm" ? (
        <input
          type="number"
          min="0"
          value={displayCm}
          onChange={handleCmChange}
          placeholder={placeholder}
          className={INPUT_CLASS}
          required={required}
        />
      ) : (
        <div className="flex gap-1.5 flex-1 flex-wrap">
          <input
            type="number"
            step="1"
            min="0"
            max="8"
            value={displayFt}
            onChange={(e) => handleFtInChange(e.target.value, displayIn)}
            placeholder="ft"
            className={INPUT_CLASS}
            required={required}
          />
          <span className="text-xs text-slate-400 self-center shrink-0">
            ft
          </span>
          <input
            type="number"
            step="1"
            min="0"
            max="11"
            value={displayIn}
            onChange={(e) => handleFtInChange(displayFt, e.target.value)}
            placeholder="in"
            className={INPUT_CLASS}
          />
          <span className="text-xs text-slate-400 self-center shrink-0">
            in
          </span>
        </div>
      )}
      {name && <input type="hidden" name={name} value={valueCm} />}
    </div>
  );
}
