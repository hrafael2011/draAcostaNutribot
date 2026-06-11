import Button from "../ui/Button"
import type { WizardStep } from "../../types"

type Props = {
  step: WizardStep
  onBack: () => void
  onNext: () => void
  hideNext?: boolean
  disableNext?: boolean
}

export default function WizardNavigation({ step, onBack, onNext, hideNext, disableNext }: Props) {
  const isFirst = step === "patient"

  return (
    <div className="mt-6 flex items-center justify-between border-t border-gray-200 pt-4">
      {!isFirst ? (
        <Button variant="ghost" type="button" onClick={onBack}>
          ← Atrás
        </Button>
      ) : (
        <div />
      )}
      {!hideNext && (
        <Button type="button" onClick={onNext} disabled={disableNext}>
          Siguiente
        </Button>
      )}
    </div>
  )
}
