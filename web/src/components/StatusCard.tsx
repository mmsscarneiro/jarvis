interface StatusCardProps {
  label: string
  value: string
  sub?: string
  highlight?: 'green' | 'red' | 'none'
}

export default function StatusCard({ label, value, sub, highlight = 'none' }: StatusCardProps) {
  const subColor =
    highlight === 'green' ? 'text-green-400' :
    highlight === 'red'   ? 'text-red-400' :
                            'text-gray-500'

  return (
    <div className="bg-surface border border-border rounded-xl p-4 flex flex-col gap-1">
      <span className="text-xs text-gray-500 uppercase tracking-wider">{label}</span>
      <span className="text-lg font-semibold text-gray-100">{value}</span>
      {sub && <span className={`text-xs ${subColor}`}>{sub}</span>}
    </div>
  )
}
