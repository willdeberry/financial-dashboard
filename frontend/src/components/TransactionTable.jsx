import { useState } from 'react'
import { formatCurrency, formatDate } from '../utils/formatters.js'
import { api } from '../api.js'

const TYPE_STYLE = {
  income: 'text-green-600 dark:text-green-400',
  expense: 'text-red-600 dark:text-red-400',
  transfer: 'text-blue-600 dark:text-blue-400',
}

const COLS = [
  { key: 'date', label: 'Date' },
  { key: 'payee', label: 'Payee / Description' },
  { key: 'amount', label: 'Amount' },
  { key: 'category', label: 'Category' },
]

export default function TransactionTable({ transactions, categories, onRefresh }) {
  const [editingId, setEditingId] = useState(null)

  const handleCategoryChange = async (txId, catId) => {
    if (!catId) return
    try {
      await api.updateTransactionCategory(txId, parseInt(catId, 10))
      onRefresh()
    } catch (err) {
      alert('Failed to update: ' + err.message)
    }
    setEditingId(null)
  }

  const exportCsv = () => {
    const rows = [
      ['Date', 'Payee', 'Description', 'Amount', 'Type', 'Source', 'Category'],
      ...transactions.map(t => [
        formatDate(t.date), t.payee || '', t.description || '',
        t.amount, t.transaction_type, t.source, t.category?.name || 'Uncategorized',
      ]),
    ]
    const csv = rows.map(r => r.map(c => `"${String(c).replace(/"/g, '""')}"`).join(',')).join('\n')
    const a = Object.assign(document.createElement('a'), {
      href: URL.createObjectURL(new Blob([csv], { type: 'text/csv' })),
      download: 'transactions.csv',
    })
    a.click()
    URL.revokeObjectURL(a.href)
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 overflow-hidden">
      <div className="flex items-center justify-between px-5 py-3 border-b border-gray-200 dark:border-gray-700">
        <h3 className="font-semibold text-gray-900 dark:text-white">
          Transactions <span className="text-gray-400 dark:text-gray-500 font-normal text-sm">({transactions.length})</span>
        </h3>
        <button
          onClick={exportCsv}
          className="px-3 py-1.5 text-xs font-medium bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 rounded-md transition-colors"
        >
          Export CSV
        </button>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-gray-50 dark:bg-gray-750 border-b border-gray-200 dark:border-gray-700">
              {COLS.map(col => (
                <th key={col.key} className="px-5 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  {col.label}
                </th>
              ))}
              <th className="px-5 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Type</th>
              <th className="px-5 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Source</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
            {transactions.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-5 py-12 text-center text-gray-400 dark:text-gray-500 text-sm">
                  No transactions found. Upload a statement to get started.
                </td>
              </tr>
            ) : transactions.map(t => (
              <tr key={t.id} className="hover:bg-gray-50 dark:hover:bg-gray-750 transition-colors group">
                <td className="px-5 py-3 whitespace-nowrap text-gray-600 dark:text-gray-400 text-xs">
                  {formatDate(t.date)}
                </td>
                <td className="px-5 py-3 max-w-xs">
                  <div className="font-medium text-gray-900 dark:text-white truncate">{t.payee || '—'}</div>
                  {t.description && t.description !== t.payee && (
                    <div className="text-xs text-gray-400 dark:text-gray-500 truncate">{t.description}</div>
                  )}
                </td>
                <td className={`px-5 py-3 whitespace-nowrap font-semibold ${TYPE_STYLE[t.transaction_type]}`}>
                  {t.transaction_type === 'income' ? '+' : t.transaction_type === 'expense' ? '−' : ''}
                  {formatCurrency(t.amount)}
                </td>
                <td className="px-5 py-3">
                  {editingId === t.id ? (
                    <select
                      defaultValue={t.category_id || ''}
                      onChange={e => handleCategoryChange(t.id, e.target.value)}
                      onBlur={() => setEditingId(null)}
                      autoFocus
                      className="text-sm rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-2 py-0.5 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="">Uncategorized</option>
                      {categories.map(c => (
                        <option key={c.id} value={c.id}>{c.name}</option>
                      ))}
                    </select>
                  ) : (
                    <button
                      onClick={() => setEditingId(t.id)}
                      className="flex items-center gap-1.5 group/cat"
                      title="Click to change category"
                    >
                      {t.category ? (
                        <span
                          className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium text-white"
                          style={{ backgroundColor: t.category.color || '#6b7280' }}
                        >
                          {t.category.name}
                        </span>
                      ) : (
                        <span className="text-xs text-gray-400">Uncategorized</span>
                      )}
                      <span className="text-gray-300 dark:text-gray-600 text-xs opacity-0 group-hover/cat:opacity-100 transition-opacity">✏</span>
                    </button>
                  )}
                </td>
                <td className="px-5 py-3 whitespace-nowrap text-xs text-gray-500 dark:text-gray-400 capitalize">{t.transaction_type}</td>
                <td className="px-5 py-3 whitespace-nowrap text-xs text-gray-500 dark:text-gray-400 capitalize">{t.source.replace('_', ' ')}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
