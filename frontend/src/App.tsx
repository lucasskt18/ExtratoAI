import { useCallback, useEffect, useState } from 'react'
import {
  exportCsvUrl,
  fetchCategories,
  fetchDashboard,
  fetchInbox,
  updateTransaction,
  type Category,
  type DashboardSummary,
  type InboxStatus,
} from './api/client'
import { CategoryChart } from './components/CategoryChart'
import { TransactionList } from './components/TransactionList'
import { UploadZone } from './components/UploadZone'
import { currentMonth, formatBRL, monthLabel, shiftMonth } from './lib/format'

function App() {
  const [month, setMonth] = useState(currentMonth)
  const [summary, setSummary] = useState<DashboardSummary | null>(null)
  const [categories, setCategories] = useState<Category[]>([])
  const [inbox, setInbox] = useState<InboxStatus | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  const refresh = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const [dash, cats, inboxStatus] = await Promise.all([
        fetchDashboard(month),
        fetchCategories(),
        fetchInbox(),
      ])
      setSummary(dash)
      setCategories(cats)
      setInbox(inboxStatus)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao carregar dados')
    } finally {
      setLoading(false)
    }
  }, [month])

  useEffect(() => {
    void refresh()
    const id = window.setInterval(() => {
      void fetchInbox().then(setInbox).catch(() => undefined)
    }, 8000)
    return () => window.clearInterval(id)
  }, [refresh])

  async function handleCategoryChange(txId: number, categoryId: number, remember: boolean) {
    const tx = summary?.recent_transactions.find((t) => t.id === txId)
    const pattern = tx?.description.split(/\s+/)[0]
    await updateTransaction(txId, {
      category_id: categoryId,
      remember_rule: remember,
      rule_pattern: pattern,
    })
    await refresh()
  }

  const uncategorized = summary?.uncategorized_count ?? 0

  return (
    <div className="app-shell">
      <header className="topbar rise">
        <div className="brand">
          <div className="brand-mark" aria-hidden>
            E
          </div>
          <div className="min-w-0">
            <div className="brand-title">ExtratoAI</div>
            <div className="brand-sub truncate">Faturas de cartão → visão do mês</div>
          </div>
        </div>

        <div className="flex flex-wrap items-center justify-end gap-2">
          <div className="month-control" aria-label="Selecionar mês">
            <button type="button" aria-label="Mês anterior" onClick={() => setMonth((m) => shiftMonth(m, -1))}>
              ←
            </button>
            <div className="month-label">{monthLabel(month)}</div>
            <button type="button" aria-label="Próximo mês" onClick={() => setMonth((m) => shiftMonth(m, 1))}>
              →
            </button>
          </div>
          <a href={exportCsvUrl(month)} className="btn btn-secondary">
            Exportar CSV
          </a>
        </div>
      </header>

      {error && (
        <div className="banner-error rise mt-4">
          {error}. Verifique se o backend está em http://127.0.0.1:8000
        </div>
      )}

      <section className="rise-2 mt-5 grid gap-4 lg:grid-cols-[1.15fr_0.85fr]">
        <div className="panel panel-pad">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <div className="section-label">
                {summary?.view_mode === 'billing' ? 'Total a pagar (fatura)' : 'Resumo do mês'}
              </div>
              <div className="metric">
                {loading && !summary ? '—' : formatBRL(summary?.total_spent ?? 0)}
              </div>
              {summary?.view_mode === 'billing' && (
                <p className="mt-2 text-sm font-medium text-[var(--color-muted)]">
                  Lançamentos na fatura:{' '}
                  <span className="font-bold text-[var(--color-ink-2)]">
                    {formatBRL(summary.charges_total)}
                  </span>
                  {summary.statements[0]?.period_end && (
                    <>
                      {' '}
                      · vencimento{' '}
                      {new Date(summary.statements[0].period_end + 'T12:00:00').toLocaleDateString(
                        'pt-BR',
                      )}
                    </>
                  )}
                </p>
              )}
            </div>
            <button type="button" className="btn btn-ghost" onClick={() => void refresh()}>
              {loading ? 'Atualizando…' : 'Atualizar'}
            </button>
          </div>

          <div className="mt-4 flex flex-wrap gap-2">
            <span className="chip chip-brand">{summary?.transaction_count ?? 0} transações</span>
            {uncategorized > 0 ? (
              <span className="chip chip-warn">{uncategorized} sem categoria</span>
            ) : (
              <span className="chip">Tudo categorizado</span>
            )}
            {inbox && <span className="chip">{inbox.processed_count} faturas importadas</span>}
            {summary?.view_mode === 'billing' && summary.statements[0] && (
              <span className="chip">
                {summary.statements[0].card_label || summary.statements[0].bank}
              </span>
            )}
          </div>

          <div className="mt-5">
            <UploadZone inbox={inbox} onUploaded={refresh} />
          </div>
        </div>

        <div className="panel panel-pad">
          <div className="section-label">Por categoria</div>
          <p className="mt-1 text-sm font-medium text-[var(--color-muted)]">
            {summary?.view_mode === 'billing'
              ? 'Distribuição dos lançamentos desta fatura.'
              : 'Distribuição dos gastos no período.'}
          </p>
          <div className="mt-4">
            <CategoryChart data={summary?.by_category ?? []} />
          </div>
        </div>
      </section>

      <section className="panel panel-pad rise-3 mt-4">
        <div className="mb-4 flex flex-wrap items-end justify-between gap-3">
          <div>
            <div className="section-label">Movimentações</div>
            <h2 className="mt-1 text-lg font-extrabold tracking-tight text-[var(--color-ink)]">
              {summary?.view_mode === 'billing'
                ? 'Lançamentos da fatura'
                : 'Transações do mês'}
            </h2>
          </div>
          <p className="text-sm font-medium text-[var(--color-muted)]">
            Clique na categoria para corrigir e criar regra.
          </p>
        </div>
        <TransactionList
          transactions={summary?.recent_transactions ?? []}
          categories={categories}
          onCategoryChange={(id, cat, remember) => {
            void handleCategoryChange(id, cat, remember)
          }}
        />
      </section>

      <footer className="mt-8 text-center text-xs font-medium text-[var(--color-muted-2)]">
        ExtratoAI · 100% local · seus dados ficam no seu Mac
      </footer>
    </div>
  )
}

export default App
