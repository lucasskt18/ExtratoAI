import { useState } from 'react'
import { Cell, Pie, PieChart, ResponsiveContainer } from 'recharts'
import type { CategoryBreakdown } from '../api/client'
import { formatBRL } from '../lib/format'

type Props = {
  data: CategoryBreakdown[]
}

export function CategoryChart({ data }: Props) {
  const chartData = data.filter((d) => d.total > 0)
  const total = chartData.reduce((acc, item) => acc + item.total, 0)
  const [active, setActive] = useState<CategoryBreakdown | null>(null)

  if (!chartData.length) {
    return (
      <div className="flex h-48 items-center justify-center rounded-2xl bg-[var(--color-bg)] text-sm font-medium text-[var(--color-muted)]">
        Sem gastos neste mês.
      </div>
    )
  }

  const centerLabel = active?.name ?? 'Total'
  const centerValue = active ? active.total : total
  const centerPct =
    active && total > 0 ? Math.round((active.total / total) * 100) : null

  return (
    <div className="grid gap-4">
      <div className="relative mx-auto h-44 w-full max-w-[240px]">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={chartData}
              dataKey="total"
              nameKey="name"
              innerRadius={58}
              outerRadius={78}
              paddingAngle={2}
              stroke="none"
              animationDuration={600}
              onMouseEnter={(_, index) => setActive(chartData[index] ?? null)}
              onMouseLeave={() => setActive(null)}
            >
              {chartData.map((entry) => (
                <Cell
                  key={`${entry.name}-${entry.category_id}`}
                  fill={entry.color}
                  stroke={
                    active?.category_id === entry.category_id ? 'white' : 'none'
                  }
                  strokeWidth={active?.category_id === entry.category_id ? 2 : 0}
                  style={{ cursor: 'pointer', outline: 'none' }}
                />
              ))}
            </Pie>
          </PieChart>
        </ResponsiveContainer>
        <div className="pointer-events-none absolute inset-0 flex items-center justify-center">
          <div className="flex h-[6.5rem] w-[6.5rem] flex-col items-center justify-center overflow-hidden px-2 text-center">
            <span
              className={
                active
                  ? 'line-clamp-2 max-w-full text-[11px] font-semibold leading-tight text-[var(--color-muted)]'
                  : 'text-[10px] font-bold uppercase tracking-[0.12em] text-[var(--color-muted-2)]'
              }
            >
              {centerLabel}
            </span>
            <span className="mt-1 text-sm font-extrabold leading-none tabular-nums text-[var(--color-ink)]">
              {formatBRL(centerValue)}
            </span>
            {centerPct !== null && (
              <span className="mt-1 text-[11px] font-bold leading-none tabular-nums text-[var(--color-muted)]">
                {centerPct}%
              </span>
            )}
          </div>
        </div>
      </div>

      <ul className="space-y-2.5">
        {chartData.slice(0, 6).map((entry) => {
          const pct = total > 0 ? Math.round((entry.total / total) * 100) : 0
          const isActive = active?.category_id === entry.category_id
          return (
            <li
              key={`${entry.name}-${entry.category_id}`}
              className={isActive ? 'opacity-100' : active ? 'opacity-55' : 'opacity-100'}
              onMouseEnter={() => setActive(entry)}
              onMouseLeave={() => setActive(null)}
            >
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
