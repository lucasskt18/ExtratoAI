import type { Category, ReviewQueue, Transaction } from '../api/client'
import { formatBRL, formatDate } from '../lib/format'

type Props = {
  review: ReviewQueue | null
  categories: Category[]
  onCategoryChange: (txId: number, categoryId: number, remember: boolean) => void
  onMarkReviewed: (statementId: number) => void
  onDeleteStatement: (statementId: number) => void
  onRecategorize: () => void
}

export function ReviewQueuePanel({
  review,
  categories,
  onCategoryChange,
  onMarkReviewed,
  onDeleteStatement,
  onRecategorize,
}: Props) {
  if (!review) return null

  const hasItems = review.needs_review_count > 0 || review.uncategorized_count > 0
  if (!hasItems) {
    return (
      <section className="panel panel-pad rise-2 mt-4">
        <div className="section-label">Fila de revisão</div>
        <p className="mt-2 text-sm font-medium text-[var(--color-muted)]">
          Nada pendente — todas as faturas processadas e categorizadas.
        </p>
      </section>
    )
  }

  return (
    <section className="panel panel-pad rise-2 mt-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="section-label">Fila de revisão</div>
          <p className="mt-1 text-sm font-medium text-[var(--color-muted)]">
            Faturas que precisam de atenção e lançamentos sem categoria.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <span className="chip chip-warn">{review.needs_review_count} faturas</span>
          <span className="chip chip-warn">{review.uncategorized_count} sem categoria</span>
          {review.uncategorized_count > 0 && (
            <button type="button" className="btn btn-ghost" onClick={onRecategorize}>
              Reaplicar regras
            </button>
          )}
        </div>
      </div>

      {review.statements_needs_review.length > 0 && (
        <div className="mt-4 space-y-2">
          <div className="text-sm font-extrabold text-[var(--color-ink)]">Faturas em revisão</div>
          {review.statements_needs_review.map((stmt) => (
            <div
              key={stmt.id}
              className="flex flex-wrap items-center justify-between gap-2 rounded-xl border border-[var(--color-warn-border)] bg-[var(--color-warn-soft)] px-3 py-2"
            >
              <div className="min-w-0">
                <div className="truncate text-sm font-bold text-[var(--color-ink)]">
                  {stmt.card_label || stmt.bank} · {stmt.source_filename}
                </div>
                <div className="text-xs font-semibold text-[var(--color-muted)]">
                  {stmt.transaction_count} lançamentos · status needs_review
                </div>
              </div>
              <div className="flex gap-2">
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => onMarkReviewed(stmt.id)}
                >
                  Marcar ok
                </button>
                <button
                  type="button"
                  className="btn btn-ghost"
                  onClick={() => onDeleteStatement(stmt.id)}
                >
                  Apagar
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {review.uncategorized_transactions.length > 0 && (
        <div className="mt-5">
          <div className="mb-2 text-sm font-extrabold text-[var(--color-ink)]">
            Sem categoria
          </div>
          <UncategorizedList
            transactions={review.uncategorized_transactions}
            categories={categories}
            onCategoryChange={onCategoryChange}
          />
        </div>
      )}
    </section>
  )
}

function UncategorizedList({
  transactions,
  categories,
  onCategoryChange,
}: {
  transactions: Transaction[]
  categories: Category[]
  onCategoryChange: (txId: number, categoryId: number, remember: boolean) => void
}) {
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
          {transactions.map((tx) => (
            <tr key={tx.id} className="is-warn">
              <td className="whitespace-nowrap text-sm font-semibold tabular-nums text-[var(--color-muted)]">
                {formatDate(tx.date)}
              </td>
              <td>
                <div className="text-sm font-bold text-[var(--color-ink)]">{tx.description}</div>
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
          ))}
        </tbody>
      </table>
    </div>
  )
}
