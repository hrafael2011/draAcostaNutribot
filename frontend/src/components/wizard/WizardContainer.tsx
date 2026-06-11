import type { ReactNode } from "react"
import Stepper from "../ui/Stepper"
import { WIZARD_STEPS, type WizardStep } from "../../types"

type WizardContainerProps = {
  current: WizardStep
  children: ReactNode
  title: string
}

export default function WizardContainer({ current, children, title }: WizardContainerProps) {
  const visibleSteps = WIZARD_STEPS.filter(
    (s) => s.key !== "guided_style" && s.key !== "guided_macros" && s.key !== "manual_targets"
  )
  const stepIndex = visibleSteps.findIndex((s) => s.key === current)

  return (
    <div className="mx-auto w-full max-w-lg">
      <h1 className="mb-4 text-xl font-bold text-gray-800">{title}</h1>
      <div className="mb-6">
        <Stepper steps={visibleSteps} current={Math.max(0, stepIndex)} />
      </div>
      <div className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm md:p-6">
        {children}
      </div>
    </div>
  )
}
