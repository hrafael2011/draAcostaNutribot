import { useState, type ReactNode } from "react"

type AccordionProps = {
  title: string
  children: ReactNode
  defaultOpen?: boolean
}

export default function Accordion({
  title,
  children,
  defaultOpen = false,
}: AccordionProps) {
  const [open, setOpen] = useState(defaultOpen)
  return (
    <div className="rounded-lg border border-gray-200">
      <button
        type="button"
        className="flex w-full items-center justify-between rounded-lg px-4 py-3 text-left text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
        onClick={() => setOpen(!open)}
        aria-expanded={open}
      >
        {title}
        <svg
          className={`h-4 w-4 transform transition-transform ${open ? "rotate-180" : ""}`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>
      {open && <div className="border-t border-gray-200 px-4 py-3">{children}</div>}
    </div>
  )
}
