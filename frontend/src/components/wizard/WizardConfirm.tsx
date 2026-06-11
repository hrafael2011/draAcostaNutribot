import Button from "../ui/Button"
import type { WizardState } from "../../types"

type Props = { state: WizardState; onGenerate: () => void; loading: boolean }

export default function WizardConfirm({ state, onGenerate, loading }: Props) {
  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold text-gray-800">Confirmar y generar dieta</h2>

      <div className="space-y-2 rounded-lg bg-gray-50 p-3 text-sm">
        <p><span className="font-medium">Paciente:</span> {state.patientName || `#${state.patientId}`}</p>
        <p><span className="font-medium">Duración:</span> {state.durationDays} días</p>
        <p><span className="font-medium">Comidas/día:</span> {state.mealsPerDay}</p>
        <p><span className="font-medium">Modo:</span> {state.strategyMode === "auto" ? "Automático" : state.strategyMode === "guided" ? "Guiado" : "Manual"}</p>
        {state.dietStyle && <p><span className="font-medium">Estilo:</span> {state.dietStyle}</p>}
        {state.doctorInstruction && <p><span className="font-medium">Nota:</span> {state.doctorInstruction}</p>}
      </div>

      <Button onClick={onGenerate} disabled={loading} className="w-full">
        {loading ? "Generando..." : "Generar Dieta"}
      </Button>
    </div>
  )
}
