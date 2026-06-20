const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

async function request(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, options)
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Request failed' }))
    throw new Error(err.detail || 'Request failed')
  }
  if (res.status === 204) return null
  return res.json()
}

function qs(params) {
  const filtered = Object.entries(params).filter(([, v]) => v !== undefined && v !== null && v !== '')
  return filtered.length ? '?' + new URLSearchParams(filtered).toString() : ''
}

export const api = {
  getTransactions: (params = {}) => request(`/transactions${qs(params)}`),
  updateTransactionCategory: (id, categoryId) =>
    request(`/transactions/${id}/category`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ category_id: categoryId }),
    }),

  getCategories: () => request('/categories'),
  createCategory: (data) =>
    request('/categories', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }),
  updateCategory: (id, data) =>
    request(`/categories/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }),
  deleteCategory: (id, reassignTo) =>
    request(`/categories/${id}${reassignTo != null ? `?reassign_to=${reassignTo}` : ''}`, {
      method: 'DELETE',
    }),
  moveTransactions: (fromId, toId) =>
    request(`/categories/${fromId}/move-transactions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ target_category_id: toId }),
    }),

  uploadFile: (file, sourceType) => {
    const form = new FormData()
    form.append('file', file)
    form.append('source_type', sourceType)
    return request('/upload', { method: 'POST', body: form })
  },
  getUploads: () => request('/uploads'),

  getSummary: (params = {}) => request(`/analytics/summary${qs(params)}`),
  getByCategory: (params = {}) => request(`/analytics/by-category${qs(params)}`),
  getMonthlyTrend: (params = {}) => request(`/analytics/monthly-trend${qs(params)}`),
  getYearlyTrend: () => request('/analytics/yearly-trend'),
  getTopSpenders: (params = {}) => request(`/analytics/top-spenders${qs(params)}`),
}
