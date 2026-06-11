import { motion, AnimatePresence } from "framer-motion";
import { X } from "@phosphor-icons/react";
import { useToast } from "../../context/ToastContext";

const TYPE_CLASSES: Record<string, string> = {
  success: "bg-emerald-600 text-white",
  error: "bg-red-600 text-white",
  info: "bg-slate-800 text-white",
};

export function ToastContainer() {
  const { toasts, removeToast } = useToast();

  return (
    <div className="fixed bottom-4 right-4 z-[100] flex flex-col gap-2 pointer-events-none">
      <AnimatePresence mode="popLayout">
        {toasts.map((toast) => (
          <motion.div
            key={toast.id}
            layout
            initial={{ opacity: 0, y: 24, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -8, scale: 0.95 }}
            transition={{ duration: 0.25, ease: [0.16, 1, 0.3, 1] }}
            className={`rounded-xl px-4 py-3 text-sm font-medium shadow-lg flex items-center gap-3 pointer-events-auto ${TYPE_CLASSES[toast.type]}`}
          >
            <span className="flex-1">{toast.message}</span>
            <button
              type="button"
              onClick={() => removeToast(toast.id)}
              className="shrink-0 hover:opacity-80 transition-opacity"
              aria-label="Close notification"
            >
              <X size={16} weight="bold" />
            </button>
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  );
}
