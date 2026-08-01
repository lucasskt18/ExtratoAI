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
      <div className="rounded-2xl bg-[var(--color-bg)] px-4 py-12 text-center text-sm font-medium text-[var(--color-muted)]">
        Nenhuma transação neste mês. Importe uma fatura PDF para começar.
      </div>
    )
  }

  return (
    <div className="table-wrap">
      <table className="data">
        <thead>
          <tr>
            <th>Data</th>
            <th>Descrição</th>
            <th>Categoria</th>
            <th className="!text-right">Valor</th>
          </tr>
        </thead>
        <tbody>
          {transactions.map((tx) => {
            const isUncategorized =
              !tx.category || tx.category.name === 'Não categorizado'
            return (
              <tr key={tx.id} className={isUncategorized ? 'is-warn' : undefined}>
                <td className="whitespace-nowrap text-sm font-semibold tabular-nums text-[var(--color-muted)]">
                  {formatDate(tx.date)}
                </td>
                <td>
                  <div className="text-sm font-bold text-[var(--color-ink)]">{tx.description}</div>
                  {tx.installment && (
                    <div className="mt-0.5 text-xs font-semibold text-[var(--color-muted-2)]">
                      Parcela {tx.installment}
                    </div>
                  )}
                </td>
                <td>
                  <select
                    className="select"
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
                <td className="text-right text-sm font-extrabold tabular-nums text-[var(--color-ink)]">
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
