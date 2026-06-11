type StepperProps = {
  steps: { label: string }[]
  current: number
}

export default function Stepper({ steps, current }: StepperProps) {
  return (
    <nav aria-label="Progress" className="w-full">
      {/* Mobile: dots */}
      <ol className="flex items-center justify-center gap-1 md:hidden">
        {steps.map((_s, i) => (
          <li key={i}>
            <span
              className={`flex h-6 w-6 items-center justify-center rounded-full text-xs font-medium
                ${i <= current ? "bg-emerald-600 text-white" : "bg-gray-200 text-gray-500"}`}
              aria-current={i === current ? "step" : undefined}
            >
              {i + 1}
            </span>
          </li>
        ))}
      </ol>
      {/* Desktop: labels */}
      <ol className="hidden md:flex items-center gap-2">
        {steps.map((s, i) => (
          <li key={i} className="flex items-center gap-2">
            <span
              className={`flex h-7 w-7 items-center justify-center rounded-full text-xs font-bold
                ${i < current ? "bg-emerald-600 text-white" : i === current ? "bg-emerald-600 text-white ring-4 ring-emerald-100" : "bg-gray-200 text-gray-500"}`}
            >
              {i < current ? "✓" : i + 1}
            </span>
            <span
              className={`text-sm ${i <= current ? "font-semibold text-emerald-700" : "text-gray-400"}`}
            >
              {s.label}
            </span>
            {i < steps.length - 1 && (
              <span className="mx-1 h-px w-8 bg-gray-300 hidden lg:block" />
            )}
          </li>
        ))}
      </ol>
    </nav>
  )
}
