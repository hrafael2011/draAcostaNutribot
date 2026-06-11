import Button from "../ui/Button"

type Props = {
  value: string
  onChange: (v: string) => void
  onSkip: () => void
}

export default function WizardNoteStep({ value, onChange, onSkip }: Props) {
  return (
    <div className="space-y-4">
      <p className="text-sm text-gray-600">
        ¿Quieres agregar una nota para orientar la generación de la dieta? Es opcional.
      </p>
      <textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        rows={3}
        placeholder="Ej: Evitar lácteos, usar alimentos económicos, incluir batidos..."
        className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
      />
      <Button variant="ghost" type="button" onClick={onSkip} className="w-full">
        Saltar este paso
      </Button>
    </div>
  )
}
