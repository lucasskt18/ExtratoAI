import {
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
} from 'recharts'
import type { CategoryBreakdown } from '../api/client'
import { formatBRL } from '../lib/format'

type Props = {
  data: CategoryBreakdown[]
}

export function CategoryChart({ data }: Props) {
  const chartData = data.filter((d) => d.total > 0)

  if (!chartData.length) {
    return (
      <div className="flex h-56 items-center justify-center text-sm text-[var(--color-muted)]">
        Sem gastos neste mês ainda.
      </div>
    )
  }

  return (
    <div className="grid gap-4 md:grid-cols-[1fr_1.1fr] items-center">
      <div className="h-56">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={chartData}
              dataKey="total"
              nameKey="name"
              innerRadius={55}
              outerRadius={90}
              paddingAngle={2}
              stroke="none"
            >
              {chartData.map((entry) => (
                <Cell key={`${entry.name}-${entry.category_id}`} fill={entry.color} />
              ))}
            </Pie>
            <Tooltip
              formatter={(value) => formatBRL(Number(value))}
              contentStyle={{
                borderRadius: 12,
                border: '1px solid var(--color-line)',
                background: 'var(--color-panel)',
              }}
            />
          </PieChart>
        </ResponsiveContainer>
      </div>
      <ul className="space-y-2">
        {chartData.map((entry) => (
          <li key={`${entry.name}-${entry.category_id}`} className="flex items-center gap-3 text-sm">
            <span
              className="h-2.5 w-2.5 rounded-full shrink-0"
              style={{ background: entry.color }}
            />
            <span className="flex-1 text-[var(--color-muted)]">{entry.name}</span>
            <span className="font-medium tabular-nums">{formatBRL(entry.total)}</span>
          </li>
        ))}
      </ul>
    </div>
  )
}
