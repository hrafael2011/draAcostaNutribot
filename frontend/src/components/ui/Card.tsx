import type { ReactNode, HTMLAttributes } from "react"

type CardProps = HTMLAttributes<HTMLDivElement> & {
  children: ReactNode
  selected?: boolean
}

export default function Card({
  children,
  selected = false,
  className = "",
  ...props
}: CardProps) {
  return (
    <div
      className={`rounded-xl border bg-white p-4 transition-shadow
        ${selected ? "border-emerald-500 bg-emerald-50 shadow-md ring-1 ring-emerald-500" : "border-gray-200 shadow-sm hover:shadow-md"}
        ${className}`}
      {...props}
    >
      {children}
    </div>
  )
}
