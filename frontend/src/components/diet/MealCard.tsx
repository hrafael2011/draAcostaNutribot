type Props = { label: string; content: string }

export default function MealCard({ label, content }: Props) {
  return (
    <div className="rounded-lg border border-gray-100 bg-white px-3 py-2">
      <p className="text-xs font-semibold text-emerald-700">{label}</p>
      <p className="mt-0.5 text-sm text-gray-700 whitespace-pre-wrap">{content}</p>
    </div>
  )
}
