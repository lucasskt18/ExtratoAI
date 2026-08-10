import { useState, type FormEvent } from 'react'
import type { Category, MerchantRule } from '../api/client'

type Props = {
  categories: Category[]
  rules: MerchantRule[]
  onUpdateCategory: (id: number, keywords: string) => Promise<void>
  onCreateRule: (pattern: string, categoryId: number) => Promise<void>
  onDeleteRule: (id: number) => Promise<void>
}

export function RulesPanel({
  categories,
  rules,
  onUpdateCategory,
  onCreateRule,
  onDeleteRule,
}: Props) {
  const [open, setOpen] = useState(false)
  const [pattern, setPattern] = useState('')
  const [ruleCategoryId, setRuleCategoryId] = useState<number | ''>('')
  const [editingId, setEditingId] = useState<number | null>(null)
  const [keywordsDraft, setKeywordsDraft] = useState('')
  const [busy, setBusy] = useState(false)

  const editableCategories = categories.filter((c) => c.name !== 'Não categorizado')

  async function handleCreate(e: FormEvent) {
    e.preventDefault()
    if (!pattern.trim() || !ruleCategoryId) return
    setBusy(true)
    try {
      await onCreateRule(pattern.trim(), Number(ruleCategoryId))
      setPattern('')
    } finally {
      setBusy(false)
    }
  }

  async function handleSaveKeywords(categoryId: number) {
    setBusy(true)
    try {
      await onUpdateCategory(categoryId, keywordsDraft)
      setEditingId(null)
    } finally {
      setBusy(false)
    }
  }

  return (
    <section className="panel panel-pad rise-3 mt-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <div className="section-label">Regras e palavras-chave</div>
          <p className="mt-1 text-sm font-medium text-[var(--color-muted)]">
            Ajuste merchants lembrados e keywords das categorias.
          </p>
        </div>
        <button type="button" className="btn btn-ghost" onClick={() => setOpen((v) => !v)}>
          {open ? 'Ocultar' : 'Gerenciar'}
        </button>
      </div>

      {open && (
        <div className="mt-4 grid gap-6 lg:grid-cols-2">
          <div>
            <div className="mb-2 text-sm font-extrabold text-[var(--color-ink)]">
              Regras de merchant ({rules.length})
            </div>
            <form className="mb-3 flex flex-wrap gap-2" onSubmit={(e) => void handleCreate(e)}>
              <input
                className="select min-w-[10rem] flex-1"
                placeholder="ex: ifood"
                value={pattern}
                onChange={(e) => setPattern(e.target.value)}
              />
              <select
                className="select"
                value={ruleCategoryId}
                onChange={(e) => setRuleCategoryId(e.target.value ? Number(e.target.value) : '')}
              >
                <option value="">Categoria…</option>
                {editableCategories.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name}
                  </option>
                ))}
              </select>
              <button type="submit" className="btn btn-secondary" disabled={busy}>
                Adicionar
              </button>
            </form>
            {rules.length === 0 ? (
              <p className="text-sm font-medium text-[var(--color-muted)]">
                Nenhuma regra ainda. Corrija uma categoria e escolha “lembrar”.
              </p>
            ) : (
              <ul className="space-y-2">
                {rules.map((rule) => {
                  const cat = categories.find((c) => c.id === rule.category_id)
                  return (
                    <li
                      key={rule.id}
                      className="flex items-center justify-between gap-2 rounded-xl border border-[var(--color-border)] bg-[var(--color-bg)] px-3 py-2"
                    >
                      <div className="min-w-0">
                        <div className="truncate text-sm font-bold text-[var(--color-ink)]">
                          {rule.pattern}
                        </div>
                        <div className="text-xs font-semibold text-[var(--color-muted)]">
                          {cat?.name ?? `categoria #${rule.category_id}`}
                        </div>
                      </div>
                      <button
                        type="button"
                        className="btn btn-ghost"
                        onClick={() => void onDeleteRule(rule.id)}
                      >
                        Remover
                      </button>
                    </li>
                  )
                })}
              </ul>
            )}
          </div>

          <div>
            <div className="mb-2 text-sm font-extrabold text-[var(--color-ink)]">
              Keywords por categoria
            </div>
            <ul className="space-y-2">
              {editableCategories.map((cat) => (
                <li
                  key={cat.id}
                  className="rounded-xl border border-[var(--color-border)] bg-[var(--color-bg)] px-3 py-2"
                >
                  <div className="flex items-center justify-between gap-2">
                    <div className="text-sm font-bold text-[var(--color-ink)]">{cat.name}</div>
                    {editingId === cat.id ? (
                      <button
                        type="button"
                        className="btn btn-secondary"
                        disabled={busy}
                        onClick={() => void handleSaveKeywords(cat.id)}
                      >
                        Salvar
                      </button>
                    ) : (
                      <button
                        type="button"
                        className="btn btn-ghost"
                        onClick={() => {
                          setEditingId(cat.id)
                          setKeywordsDraft(cat.keywords ?? '')
                        }}
                      >
                        Editar
                      </button>
                    )}
                  </div>
                  {editingId === cat.id ? (
                    <textarea
                      className="select mt-2 min-h-[4.5rem] w-full resize-y"
                      value={keywordsDraft}
                      onChange={(e) => setKeywordsDraft(e.target.value)}
                      placeholder="ifood,rappi,uber eats"
                    />
                  ) : (
                    <p className="mt-1 text-xs font-medium text-[var(--color-muted)]">
                      {cat.keywords?.trim() ? cat.keywords : 'Sem keywords'}
                    </p>
                  )}
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}
    </section>
  )
}
