import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from 'recharts'
import type { CategoryBreakdown } from '../api/client'
import { formatBRL } from '../lib/format'

type Props = {
  data: CategoryBreakdown[]
}

export function CategoryChart({ data }: Props) {
  const chartData = data.filter((d) => d.total > 0)
  const total = chartData.reduce((acc, item) => acc + item.total, 0)

  if (!chartData.length) {
    return (
      <div className="flex h-48 items-center justify-center rounded-2xl bg-[var(--color-bg)] text-sm font-medium text-[var(--color-muted)]">
        Sem gastos neste mês.
      </div>
    )
  }

  return (
    <div className="grid gap-4">
      <div className="relative mx-auto h-44 w-full max-w-[240px]">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={chartData}
              dataKey="total"
              nameKey="name"
              innerRadius={52}
              outerRadius={78}
              paddingAngle={2}
              stroke="none"
              animationDuration={600}
            >
              {chartData.map((entry) => (
                <Cell key={`${entry.name}-${entry.category_id}`} fill={entry.color} />
              ))}
            </Pie>
            <Tooltip
              formatter={(value) => formatBRL(Number(value))}
              contentStyle={{
                borderRadius: 12,
                border: '1px solid var(--color-border)',
                background: 'white',
                fontSize: 13,
                fontWeight: 600,
              }}
            />
          </PieChart>
        </ResponsiveContainer>
        <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-[10px] font-bold uppercase tracking-[0.12em] text-[var(--color-muted-2)]">
            Total
          </span>
          <span className="mt-0.5 text-sm font-extrabold tabular-nums text-[var(--color-ink)]">
            {formatBRL(total)}
          </span>
        </div>
      </div>

      <ul className="space-y-2.5">
        {chartData.slice(0, 6).map((entry) => {
          const pct = total > 0 ? Math.round((entry.total / total) * 100) : 0
          return (
            <li key={`${entry.name}-${entry.category_id}`}>
              <div className="mb-1 flex items-center justify-between gap-3 text-sm">
                <span className="flex min-w-0 items-center gap-2 font-semibold text-[var(--color-ink-2)]">
                  <span
                    className="h-2.5 w-2.5 shrink-0 rounded-full"
                    style={{ background: entry.color }}
                  />
                  <span className="truncate">{entry.name}</span>
                </span>
                <span className="shrink-0 font-bold tabular-nums text-[var(--color-ink)]">
                  {formatBRL(entry.total)}
                </span>
              </div>
              <div className="flex items-center gap-2">
                <div className="bar-track flex-1">
                  <div
                    className="bar-fill"
                    style={{ width: `${pct}%`, background: entry.color }}
                  />
                </div>
                <span className="w-8 text-right text-xs font-bold tabular-nums text-[var(--color-muted)]">
                  {pct}%
                </span>
              </div>
            </li>
          )
        })}
      </ul>
    </div>
  )
}
