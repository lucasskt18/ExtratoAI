export type Category = {
  id: number
  name: string
  color: string
  keywords: string
}

export type Transaction = {
  id: number
  statement_id: number
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
  count: number
}

export type DashboardSummary = {
  month: string
  total_spent: number
  transaction_count: number
  uncategorized_count: number
  by_category: CategoryBreakdown[]
  recent_transactions: Transaction[]
}

export type Statement = {
  id: number
  bank: string
  card_label?: string | null
  period_start?: string | null
  period_end?: string | null
  total_amount: number
  source_filename: string
  file_hash: string
  status: string
  created_at: string
  transaction_count: number
}

export type InboxStatus = {
  inbox_dir: string
  pending_pdfs: string[]
  processed_count: number
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

export function exportCsvUrl(month: string) {
  return `${API}/export/csv?month=${encodeURIComponent(month)}`
}
