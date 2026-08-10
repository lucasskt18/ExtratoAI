export type Category = {
  id: number
  name: string
  color?: string
  keywords?: string
}

export type MerchantRule = {
  id: number
  pattern: string
  category_id: number
}

export type Transaction = {
  id: number
  statement_id?: number
  date: string
  description: string
  amount: number
  installment?: string | null
  category_id?: number | null
  category?: Category | null
}

export type CategoryBreakdown = {
  category_id: number | null
  name: string
  color: string
  total: number
}

export type Statement = {
  id: number
  bank: string
  card_label?: string | null
  period_end?: string | null
  source_filename: string
  status?: string
  transaction_count?: number
}

export type DashboardSummary = {
  total_spent: number
  charges_total: number
  view_mode: 'calendar' | 'billing'
  transaction_count: number
  uncategorized_count: number
  by_category: CategoryBreakdown[]
  recent_transactions: Transaction[]
  statements: Statement[]
}

export type InboxStatus = {
  pending_pdfs: string[]
  processed_count: number
}

export type ReviewQueue = {
  statements_needs_review: Statement[]
  uncategorized_transactions: Transaction[]
  needs_review_count: number
  uncategorized_count: number
}

const API = '/api'

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API}${path}`, init)
  if (!res.ok) {
    let detail = res.statusText
    try {
      const body = await res.json()
      detail = body.detail || JSON.stringify(body)
    } catch {
      /* ignore */
    }
    throw new Error(detail)
  }
  return res.json() as Promise<T>
}

export function fetchDashboard(month: string) {
  return request<DashboardSummary>(`/dashboard?month=${encodeURIComponent(month)}`)
}

export function fetchCategories() {
  return request<Category[]>('/categories')
}

export function fetchInbox() {
  return request<InboxStatus>('/statements/inbox')
}

export function fetchReviewQueue() {
  return request<ReviewQueue>('/review')
}

export function fetchMerchantRules() {
  return request<MerchantRule[]>('/categories/rules')
}

export async function uploadPdf(file: File) {
  const form = new FormData()
  form.append('file', file)
  return request<{ statement: Statement; message: string }>('/statements/upload', {
    method: 'POST',
    body: form,
  })
}

export function updateTransaction(
  id: number,
  payload: { category_id: number; remember_rule?: boolean; rule_pattern?: string },
) {
  return request<Transaction>(`/transactions/${id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}

export function updateCategory(id: number, payload: { keywords?: string; name?: string; color?: string }) {
  return request<Category>(`/categories/${id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}

export function createMerchantRule(pattern: string, categoryId: number) {
  return request<MerchantRule>('/categories/rules', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ pattern, category_id: categoryId }),
  })
}

export function deleteMerchantRule(id: number) {
  return request<{ status: string }>(`/categories/rules/${id}`, { method: 'DELETE' })
}

export function markStatementReviewed(id: number) {
  return request<Statement>(`/review/statements/${id}/mark-reviewed`, { method: 'POST' })
}

export function deleteStatement(id: number) {
  return request<{ status: string }>(`/statements/${id}`, { method: 'DELETE' })
}

export function recategorizeUncategorized() {
  return request<{ updated: number }>('/categories/recategorize', { method: 'POST' })
}

export function exportCsvUrl(month: string) {
  return `${API}/export/csv?month=${encodeURIComponent(month)}`
}
