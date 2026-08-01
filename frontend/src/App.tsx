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

  return (
    <div className="mx-auto min-h-screen max-w-5xl px-4 py-8 md:px-6 md:py-12">
      <header className="animate-fade-up mb-8 flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.22em] text-[var(--color-accent)]">
            Finanças pessoais
          </p>
          <h1 className="mt-1 font-[family-name:var(--font-display)] text-4xl font-semibold tracking-tight md:text-5xl">
            ExtratoAI
          </h1>
          <p className="mt-2 max-w-md text-[var(--color-muted)]">
            Faturas de cartão viram visão clara do mês — sem abrir vários apps.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => setMonth((m) => shiftMonth(m, -1))}
            className="rounded-lg border border-[var(--color-line)] bg-[var(--color-panel)] px-3 py-2 text-sm hover:border-[var(--color-accent)]"
          >
            ←
          </button>
          <div className="min-w-[160px] text-center font-[family-name:var(--font-display)] text-lg capitalize">
            {monthLabel(month)}
          </div>
          <button
            type="button"
            onClick={() => setMonth((m) => shiftMonth(m, 1))}
            className="rounded-lg border border-[var(--color-line)] bg-[var(--color-panel)] px-3 py-2 text-sm hover:border-[var(--color-accent)]"
          >
            →
          </button>
        </div>
      </header>

      <UploadZone inbox={inbox} onUploaded={refresh} />

      {error && (
        <p className="mt-4 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
          {error}. Confira se o backend está em http://127.0.0.1:8000
        </p>
      )}

      <section className="animate-fade-up mt-8 grid gap-4 md:grid-cols-3">
        <div className="md:col-span-2 rounded-2xl border border-[var(--color-line)] bg-[var(--color-panel)]/80 px-5 py-5">
          <p className="text-sm text-[var(--color-muted)]">Total gasto no mês</p>
          <p className="mt-1 font-[family-name:var(--font-display)] text-4xl font-semibold tabular-nums">
            {loading && !summary ? '…' : formatBRL(summary?.total_spent ?? 0)}
          </p>
          <p className="mt-2 text-sm text-[var(--color-muted)]">
            {summary?.transaction_count ?? 0} transações
            {(summary?.uncategorized_count ?? 0) > 0 && (
              <span className="ml-2 text-[var(--color-warn)]">
                · {summary?.uncategorized_count} sem categoria
              </span>
            )}
          </p>
        </div>
        <div className="rounded-2xl border border-[var(--color-line)] bg-[var(--color-panel)]/80 px-5 py-5 flex flex-col justify-between">
          <div>
            <p className="text-sm text-[var(--color-muted)]">Exportar</p>
            <p className="mt-1 font-[family-name:var(--font-display)] text-xl">Planilha CSV</p>
          </div>
          <a
            href={exportCsvUrl(month)}
            className="mt-4 inline-flex items-center justify-center rounded-xl bg-[var(--color-accent)] px-4 py-2.5 text-sm font-medium text-white transition hover:opacity-90"
          >
            Baixar CSV do mês
          </a>
        </div>
      </section>

      <section className="animate-fade-up-delay mt-6 rounded-2xl border border-[var(--color-line)] bg-[var(--color-panel)]/80 px-5 py-5">
        <h2 className="font-[family-name:var(--font-display)] text-2xl">Por categoria</h2>
        <p className="mt-1 text-sm text-[var(--color-muted)]">
          Onde o dinheiro foi neste período.
        </p>
        <div className="mt-4">
          <CategoryChart data={summary?.by_category ?? []} />
        </div>
      </section>

      <section className="animate-fade-up-delay mt-6 rounded-2xl border border-[var(--color-line)] bg-[var(--color-panel)]/80 px-5 py-5">
        <div className="mb-4 flex items-end justify-between gap-3">
          <div>
            <h2 className="font-[family-name:var(--font-display)] text-2xl">Transações</h2>
            <p className="mt-1 text-sm text-[var(--color-muted)]">
              Ajuste categorias — linhas em destaque ainda precisam de atenção.
            </p>
          </div>
          <button
            type="button"
            onClick={() => void refresh()}
            className="rounded-lg border border-[var(--color-line)] px-3 py-1.5 text-sm hover:border-[var(--color-accent)]"
          >
            Atualizar
          </button>
        </div>
        <TransactionList
          transactions={summary?.recent_transactions ?? []}
          categories={categories}
          onCategoryChange={(id, cat, remember) => {
            void handleCategoryChange(id, cat, remember)
          }}
        />
      </section>

      <footer className="mt-10 text-center text-xs text-[var(--color-muted)]">
        ExtratoAI · dados locais · e-mail IMAP planejado para v1.1
      </footer>
    </div>
  )
}

export default App
