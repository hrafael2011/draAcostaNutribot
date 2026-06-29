import { useState, useCallback, type FormEvent } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { X, CaretDown, CaretUp, Spinner } from "@phosphor-icons/react";
import { createPatient, patchProfile, addMetric } from "../../services/api";
import { useToast } from "../../context/ToastContext";
import type { Patient } from "../../types";
import DatePicker from "../ui/DatePicker"
import LocationSelector from "../LocationSelector";
import OptionalField from "../ui/OptionalField";
import WeightInput from "../ui/WeightInput";
import HeightInput from "../ui/HeightInput";
import { OBJECTIVE_OPTIONS } from "../../constants/objectives";

type PatientDrawerProps = {
  open: boolean;
  onClose: () => void;
  onCreated: (patient: Patient) => void;
};

interface PatientFormData {
  first_name: string;
  last_name: string;
  birth_date: string;
  sex: string;
  country: string;
  city: string;
  whatsapp: string;
  email: string;
  objective: string;
  diseases: string;
  medications: string;
  food_allergies: string;
  foods_avoided: string;
  dietary_style: string;
  weight_kg: string;
  height_cm: string;
}

interface FormErrors {
  first_name?: string;
  last_name?: string;
}

const INITIAL_FORM: PatientFormData = {
  first_name: "",
  last_name: "",
  birth_date: "",
  sex: "",
  country: "",
  city: "",
  whatsapp: "",
  email: "",
  objective: "",
  diseases: "",
  medications: "",
  food_allergies: "",
  foods_avoided: "",
  dietary_style: "",
  weight_kg: "",
  height_cm: "",
};

const DIETARY_STYLES: { value: string; label: string }[] = [
  { value: "", label: "Sin especificar" },
  { value: "Equilibrada", label: "Equilibrada" },
  { value: "Baja en carbohidratos", label: "Baja en carbohidratos" },
  { value: "Alta en carbohidratos", label: "Alta en carbohidratos" },
  { value: "Alta en proteína", label: "Alta en proteína" },
  { value: "Mediterránea", label: "Mediterránea" },
];

const SEX_OPTIONS: { value: string; label: string }[] = [
  { value: "", label: "No especificar" },
  { value: "Femenino", label: "Femenino" },
  { value: "Masculino", label: "Masculino" },
];

const INPUT_CLASS =
  "w-full px-3.5 py-2.5 text-sm border border-slate-200 rounded-xl bg-white text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-colors";

const LABEL_CLASS = "block text-sm font-medium text-slate-700 mb-1.5";

const ERROR_CLASS = "text-xs text-red-500 mt-1";

export default function PatientDrawer({ open, onClose, onCreated }: PatientDrawerProps) {
  const { addToast } = useToast();

  const [form, setForm] = useState<PatientFormData>(INITIAL_FORM);
  const [errors, setErrors] = useState<FormErrors>({});
  const [saving, setSaving] = useState(false);
  const [clinicalOpen, setClinicalOpen] = useState(false);
  const [metricsOpen, setMetricsOpen] = useState(false);

  const resetForm = useCallback(() => {
    setForm(INITIAL_FORM);
    setErrors({});
    setClinicalOpen(false);
    setMetricsOpen(false);
  }, []);

  const handleClose = useCallback(() => {
    if (saving) return;
    resetForm();
    onClose();
  }, [saving, resetForm, onClose]);

  const setField = useCallback(
    (field: keyof PatientFormData) =>
      (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
        setForm((prev) => ({ ...prev, [field]: e.target.value }));
      },
    [],
  );

  const anyClinicalFieldFilled = (): boolean => {
    return (
      form.objective !== "" ||
      form.diseases !== "" ||
      form.medications !== "" ||
      form.food_allergies !== "" ||
      form.foods_avoided !== "" ||
      form.dietary_style !== ""
    );
  };

  const anyMetricFieldFilled = (): boolean => {
    return form.weight_kg !== "" || form.height_cm !== "";
  };

  const handleSave = async (e: FormEvent) => {
    e.preventDefault();

    const newErrors: FormErrors = {};
    if (!form.first_name.trim()) {
      newErrors.first_name = "El nombre es obligatorio";
    }
    if (!form.last_name.trim()) {
      newErrors.last_name = "El apellido es obligatorio";
    }
    setErrors(newErrors);
    if (Object.keys(newErrors).length > 0) return;

    setSaving(true);

    try {
      const patient = await createPatient({
        first_name: form.first_name.trim(),
        last_name: form.last_name.trim(),
        birth_date: form.birth_date || undefined,
        sex: form.sex || undefined,
        country: form.country || undefined,
        city: form.city || undefined,
        whatsapp: form.whatsapp || undefined,
        email: form.email || undefined,
      });

      if (anyClinicalFieldFilled()) {
        const profileBody: Record<string, unknown> = {};
        if (form.objective) profileBody.objective = form.objective;
        if (form.diseases) profileBody.diseases = form.diseases;
        if (form.medications) profileBody.medications = form.medications;
        if (form.food_allergies) profileBody.food_allergies = form.food_allergies;
        if (form.foods_avoided) profileBody.foods_avoided = form.foods_avoided;
        if (form.dietary_style) profileBody.dietary_style = form.dietary_style;
        await patchProfile(patient.id, profileBody);
      }

      if (anyMetricFieldFilled()) {
        const metricBody: Record<string, unknown> = { source: "admin" };
        if (form.weight_kg) metricBody.weight_kg = parseFloat(form.weight_kg);
        if (form.height_cm) metricBody.height_cm = parseFloat(form.height_cm);
        await addMetric(patient.id, metricBody);
      }

      addToast("Paciente creado exitosamente", "success");
      resetForm();
      onCreated(patient);
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Error al crear paciente";
      addToast(message, "error");
    } finally {
      setSaving(false);
    }
  };

  return (
    <AnimatePresence>
      {open && (
        <>
          {/* Backdrop */}
          <motion.div
            key="drawer-backdrop"
            className="fixed inset-0 bg-black/20 backdrop-blur-sm z-50"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={handleClose}
          />

          {/* Panel */}
          <motion.div
            key="drawer-panel"
            className="fixed right-0 top-0 bottom-0 w-full md:w-[480px] max-w-full bg-white shadow-xl z-50 flex flex-col"
            initial={{ x: "100%" }}
            animate={{ x: 0 }}
            exit={{ x: "100%" }}
            transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
          >
            {/* Header */}
            <div className="flex justify-between items-center px-6 py-4 border-b border-slate-200 shrink-0">
              <h2 className="text-lg font-semibold text-slate-800">
                Nuevo Paciente
              </h2>
              <button
                type="button"
                onClick={handleClose}
                disabled={saving}
                className="p-2 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                aria-label="Cerrar"
              >
                <X size={20} />
              </button>
            </div>

            {/* Body */}
            <form
              onSubmit={handleSave}
              className="flex-1 flex flex-col overflow-hidden"
            >
              <div className="flex-1 overflow-y-auto p-6 space-y-6">
                {/* Section 1: Datos personales */}
                <div className="space-y-4">
                  <h3 className="text-sm font-semibold text-slate-800 uppercase tracking-wide">
                    Datos personales
                  </h3>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label htmlFor="drawer-first-name" className={LABEL_CLASS}>
                        Nombre <span className="text-red-500">*</span>
                      </label>
                      <input
                        id="drawer-first-name"
                        type="text"
                        value={form.first_name}
                        onChange={setField("first_name")}
                        placeholder="Ej. Juan"
                        className={INPUT_CLASS}
                      />
                      {errors.first_name && (
                        <p className={ERROR_CLASS}>{errors.first_name}</p>
                      )}
                    </div>
                    <div>
                      <label htmlFor="drawer-last-name" className={LABEL_CLASS}>
                        Apellido <span className="text-red-500">*</span>
                      </label>
                      <input
                        id="drawer-last-name"
                        type="text"
                        value={form.last_name}
                        onChange={setField("last_name")}
                        placeholder="Ej. Pérez"
                        className={INPUT_CLASS}
                      />
                      {errors.last_name && (
                        <p className={ERROR_CLASS}>{errors.last_name}</p>
                      )}
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label htmlFor="drawer-birth-date" className={LABEL_CLASS}>
                        Fecha nacimiento
                      </label>
                      <DatePicker
                        value={form.birth_date}
                        onChange={(iso) => setForm((prev) => ({ ...prev, birth_date: iso }))}
                        placeholder="DD/MM/AAAA"
                      />
                    </div>
                    <div>
                      <label htmlFor="drawer-sex" className={LABEL_CLASS}>
                        Sexo
                      </label>
                      <select
                        id="drawer-sex"
                        value={form.sex}
                        onChange={setField("sex")}
                        className={INPUT_CLASS}
                      >
                        {SEX_OPTIONS.map((o) => (
                          <option key={o.value} value={o.value}>
                            {o.label}
                          </option>
                        ))}
                      </select>
                    </div>
                  </div>

                  <LocationSelector
                    country={form.country}
                    city={form.city}
                    onCountryChange={(c) => { setForm((prev) => ({ ...prev, country: c, city: "" })) }}
                    onCityChange={(c) => setForm((prev) => ({ ...prev, city: c }))}
                  />

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label htmlFor="drawer-whatsapp" className={LABEL_CLASS}>
                        WhatsApp
                      </label>
                      <input
                        id="drawer-whatsapp"
                        type="text"
                        value={form.whatsapp}
                        onChange={setField("whatsapp")}
                        placeholder="Ej. +54 11 1234 5678"
                        className={INPUT_CLASS}
                      />
                    </div>
                    <div>
                      <label htmlFor="drawer-email" className={LABEL_CLASS}>
                        Email
                      </label>
                      <input
                        id="drawer-email"
                        type="email"
                        value={form.email}
                        onChange={setField("email")}
                        placeholder="ejemplo@correo.com"
                        className={INPUT_CLASS}
                      />
                    </div>
                  </div>
                </div>

                {/* Section 2: Perfil clínico */}
                <div className="border-t border-slate-100 pt-6">
                  <button
                    type="button"
                    onClick={() => setClinicalOpen(!clinicalOpen)}
                    className="flex items-center justify-between w-full text-left"
                  >
                    <span className="text-sm font-semibold text-slate-800 uppercase tracking-wide">
                      Perfil clínico (opcional)
                    </span>
                    {clinicalOpen ? (
                      <CaretUp size={16} className="text-slate-400 shrink-0" />
                    ) : (
                      <CaretDown size={16} className="text-slate-400 shrink-0" />
                    )}
                  </button>

                  <AnimatePresence initial={false}>
                    {clinicalOpen && (
                      <motion.div
                        key="clinical"
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: "auto", opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        transition={{ duration: 0.25, ease: "easeInOut" }}
                        className="overflow-hidden"
                      >
                        <div className="space-y-4 pt-4">
                          <div>
                            <label htmlFor="drawer-objective" className={LABEL_CLASS}>
                              Objetivo
                            </label>
                            <select
                              id="drawer-objective"
                              value={form.objective}
                              onChange={setField("objective")}
                              className={INPUT_CLASS}
                            >
                              {OBJECTIVE_OPTIONS.map((o) => (
                                <option key={o.value} value={o.value}>
                                  {o.label}
                                </option>
                              ))}
                            </select>
                          </div>
                          <OptionalField
                            label="Enfermedades"
                            value={form.diseases}
                            onChange={(v) => setForm((prev) => ({ ...prev, diseases: v }))}
                            placeholder="Ej. Diabetes tipo 2, Hipertensión"
                          />
                          <OptionalField
                            label="Medicamentos"
                            value={form.medications}
                            onChange={(v) => setForm((prev) => ({ ...prev, medications: v }))}
                            placeholder="Ej. Metformina 500mg, Losartán 50mg"
                          />
                          <OptionalField
                            label="Alergias alimentarias"
                            value={form.food_allergies}
                            onChange={(v) => setForm((prev) => ({ ...prev, food_allergies: v }))}
                            placeholder="Ej. Mariscos, Maní"
                          />
                          <OptionalField
                            label="Alimentos a evitar"
                            value={form.foods_avoided}
                            onChange={(v) => setForm((prev) => ({ ...prev, foods_avoided: v }))}
                            placeholder="Ej. Lácteos, Gluten"
                          />
                          <div>
                            <label htmlFor="drawer-dietary-style" className={LABEL_CLASS}>
                              Estilo de alimentación
                            </label>
                            <select
                              id="drawer-dietary-style"
                              value={form.dietary_style}
                              onChange={setField("dietary_style")}
                              className={INPUT_CLASS}
                            >
                              {DIETARY_STYLES.map((s) => (
                                <option key={s.value} value={s.value}>
                                  {s.label}
                                </option>
                              ))}
                            </select>
                          </div>
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>

                {/* Section 3: Métricas iniciales */}
                <div className="border-t border-slate-100 pt-6">
                  <button
                    type="button"
                    onClick={() => setMetricsOpen(!metricsOpen)}
                    className="flex items-center justify-between w-full text-left"
                  >
                    <span className="text-sm font-semibold text-slate-800 uppercase tracking-wide">
                      Métricas iniciales (opcional)
                    </span>
                    {metricsOpen ? (
                      <CaretUp size={16} className="text-slate-400 shrink-0" />
                    ) : (
                      <CaretDown size={16} className="text-slate-400 shrink-0" />
                    )}
                  </button>

                  <AnimatePresence initial={false}>
                    {metricsOpen && (
                      <motion.div
                        key="metrics"
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: "auto", opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        transition={{ duration: 0.25, ease: "easeInOut" }}
                      >
                        <div className="space-y-4 pt-4">
                          <div>
                            <label className={LABEL_CLASS}>Peso</label>
                            <WeightInput
                              valueKg={form.weight_kg}
                              onChangeKg={(v) => setForm((prev) => ({ ...prev, weight_kg: v }))}
                              placeholder="Ej. 70.5"
                            />
                          </div>
                          <div>
                            <label className={LABEL_CLASS}>Altura</label>
                            <HeightInput
                              valueCm={form.height_cm}
                              onChangeCm={(v) => setForm((prev) => ({ ...prev, height_cm: v }))}
                              placeholder="Ej. 170"
                            />
                          </div>
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              </div>

              {/* Footer */}
              <div className="px-6 py-4 border-t border-slate-200 shrink-0">
                <button
                  type="submit"
                  disabled={saving}
                  className="w-full bg-emerald-600 text-white rounded-full py-3 text-sm font-semibold hover:bg-emerald-700 active:scale-[0.98] transition-all disabled:opacity-50 disabled:cursor-not-allowed disabled:active:scale-100 flex items-center justify-center gap-2"
                >
                  {saving ? (
                    <>
                      <Spinner size={18} className="animate-spin" />
                      Guardando...
                    </>
                  ) : (
                    "Guardar paciente"
                  )}
                </button>
              </div>
            </form>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
