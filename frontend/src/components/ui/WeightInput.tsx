import { useState, type ChangeEvent } from "react";

export const WEIGHT_LB_TO_KG = 0.45359237;

type WeightInputProps = {
  valueKg: string;
  onChangeKg: (kg: string) => void;
  name?: string;
  required?: boolean;
  placeholder?: string;
};

const INPUT_CLASS =
  "flex-1 px-3.5 py-2.5 text-sm border border-slate-200 rounded-xl bg-white text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-colors";

export default function WeightInput({
  valueKg,
  onChangeKg,
  name,
  required = false,
  placeholder = "0.0",
}: WeightInputProps) {
  const kg = parseFloat(valueKg);
  const [unit, setUnit] = useState<"kg" | "lb">("kg");

  const displayValue = (() => {
    if (!valueKg || isNaN(kg)) return "";
    if (unit === "kg") return valueKg;
    return (kg / WEIGHT_LB_TO_KG).toFixed(1);
  })();

  function handleValueChange(e: ChangeEvent<HTMLInputElement>) {
    const raw = e.target.value;
    if (raw === "" || raw === "-") {
      onChangeKg("");
      return;
    }
    const num = parseFloat(raw);
    if (isNaN(num)) return;
    const kgValue = unit === "kg" ? num : num * WEIGHT_LB_TO_KG;
    onChangeKg(kgValue.toFixed(2));
  }

  function handleUnitChange(e: ChangeEvent<HTMLSelectElement>) {
    setUnit(e.target.value as "kg" | "lb");
  }

  return (
    <div className="flex gap-2">
      <input
        type="number"
        step="0.1"
        min="0"
        value={displayValue}
        onChange={handleValueChange}
        placeholder={placeholder}
        className={INPUT_CLASS}
        required={required}
      />
      <select
        value={unit}
        onChange={handleUnitChange}
        className="px-2 py-2.5 text-sm border border-slate-200 rounded-xl bg-white text-slate-700 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-colors shrink-0"
      >
        <option value="kg">kg</option>
        <option value="lb">lb</option>
      </select>
      {name && <input type="hidden" name={name} value={valueKg} />}
    </div>
  );
}
