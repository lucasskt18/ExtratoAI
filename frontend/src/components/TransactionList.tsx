import type { Category, Transaction } from '../api/client'
import { formatBRL, formatDate } from '../lib/format'

type Props = {
  transactions: Transaction[]
  categories: Category[]
  onCategoryChange: (txId: number, categoryId: number, remember: boolean) => void
}

export function TransactionList({ transactions, categories, onCategoryChange }: Props) {
  if (!transactions.length) {
    return (
      <p className="py-10 text-center text-sm text-[var(--color-muted)]">
        Nenhuma transação neste mês. Envie uma fatura PDF para começar.
      </p>
    )
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[640px] text-left text-sm">
        <thead>
          <tr className="border-b border-[var(--color-line)] text-[var(--color-muted)]">
            <th className="py-2 pr-3 font-medium">Data</th>
            <th className="py-2 pr-3 font-medium">Descrição</th>
            <th className="py-2 pr-3 font-medium">Categoria</th>
            <th className="py-2 text-right font-medium">Valor</th>
          </tr>
        </thead>
        <tbody>
          {transactions.map((tx) => {
            const isUncategorized =
              !tx.category || tx.category.name === 'Não categorizado'
            return (
              <tr
                key={tx.id}
                className={[
                  'border-b border-[var(--color-line)]/70 transition-colors',
                  isUncategorized ? 'bg-amber-50/60' : 'hover:bg-white/50',
                ].join(' ')}
              >
                <td className="py-3 pr-3 tabular-nums text-[var(--color-muted)]">
                  {formatDate(tx.date)}
                </td>
                <td className="py-3 pr-3">
                  <div className="font-medium text-[var(--color-ink)]">{tx.description}</div>
                  {tx.installment && (
                    <div className="text-xs text-[var(--color-muted)]">Parcela {tx.installment}</div>
                  )}
                </td>
                <td className="py-3 pr-3">
                  <select
                    className="max-w-[180px] rounded-lg border border-[var(--color-line)] bg-[var(--color-panel)] px-2 py-1.5 text-sm outline-none focus:border-[var(--color-accent)]"
                    value={tx.category_id ?? ''}
                    onChange={(e) => {
                      const categoryId = Number(e.target.value)
                      if (!categoryId) return
                      const remember = window.confirm(
                        'Lembrar esta regra para descrições parecidas?',
                      )
                      onCategoryChange(tx.id, categoryId, remember)
                    }}
                  >
                    <option value="" disabled>
                      Selecionar…
                    </option>
                    {categories.map((c) => (
                      <option key={c.id} value={c.id}>
                        {c.name}
                      </option>
                    ))}
                  </select>
                </td>
                <td className="py-3 text-right font-medium tabular-nums">
                  {formatBRL(tx.amount)}
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
