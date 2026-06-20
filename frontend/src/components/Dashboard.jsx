import { useState, useEffect, useCallback } from 'react'
import { api } from '../api.js'
import Summary from './Summary.jsx'
import Filters from './Filters.jsx'
import TransactionTable from './TransactionTable.jsx'
import CategoryPie from './Charts/CategoryPie.jsx'
import MonthlyTrend from './Charts/MonthlyTrend.jsx'
import TopSpenders from './Charts/TopSpenders.jsx'

const PAGE_SIZE = 50

function ChartCard({ title, children }) {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-5">
      <h3 className="font-semibold text-gray-900 dark:text-white mb-4">{title}</h3>
      {children}
    </div>
  )
}

export default function Dashboard() {
  const [transactions, setTransactions] = useState([])
  const [categories, setCategories] = useState([])
  const [stats, setStats] = useState(null)
  const [categoryData, setCategoryData] = useState([])
  const [monthlyData, setMonthlyData] = useState([])
  const [topSpenders, setTopSpenders] = useState([])
  const [filters, setFilters] = useState({})
  const [loading, setLoading] = useState(true)
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)

  const fetchAll = useCallback(async (activeFilters = {}, currentPage = 1) => {
    setLoading(true)
    try {
      const dateParams = {
        start_date: activeFilters.start_date,
        end_date: activeFilters.end_date,
      }
      const [txRes, catRes, statsRes, byCatRes, monthlyRes, topRes] = await Promise.all([
        api.getTransactions({ ...activeFilters, page: currentPage, page_size: PAGE_SIZE }),
        api.getCategories(),
        api.getSummary(dateParams),
        api.getByCategory({ ...dateParams, transaction_type: 'expense' }),
        api.getMonthlyTrend(dateParams),
        api.getTopSpenders({ ...dateParams, limit: 8 }),
      ])
      setTransactions(txRes.items || [])
      setTotal(txRes.total || 0)
      setCategories(catRes || [])
      setStats(statsRes)
      setCategoryData(byCatRes || [])
      setMonthlyData(monthlyRes || [])
      setTopSpenders(topRes || [])
    } catch (err) {
      console.error('Dashboard load error:', err)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchAll(filters, page)
  }, [fetchAll, filters, page])

  const handleFilter = (newFilters) => {
    setFilters(newFilters)
    setPage(1)
  }

  const handleCategoryUpdated = useCallback((txId, categoryId) => {
    const category = categories.find(c => c.id === categoryId) || null
    setTransactions(prev => prev.map(t =>
      t.id === txId ? { ...t, category_id: categoryId, category } : t
    ))
  }, [categories])

  const handleBulkCategoryUpdated = useCallback((txIds, categoryId) => {
    const category = categories.find(c => c.id === categoryId) || null
    const idSet = new Set(txIds)
    setTransactions(prev => prev.map(t =>
      idSet.has(t.id) ? { ...t, category_id: categoryId, category } : t
    ))
  }, [categories])

  const totalPages = Math.ceil(total / PAGE_SIZE)

  return (
    <div className="space-y-6">
      <Summary stats={stats} />

      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
        <div className="lg:col-span-3">
          <ChartCard title="Spending by Category">
            <CategoryPie data={categoryData} />
          </ChartCard>
        </div>
        <div className="lg:col-span-2">
          <ChartCard title="Monthly Trends">
            <MonthlyTrend data={monthlyData} />
          </ChartCard>
        </div>
      </div>

      <ChartCard title="Top Spending Categories">
        <TopSpenders data={topSpenders} />
      </ChartCard>

      <Filters categories={categories} onFilter={handleFilter} />

      {loading ? (
        <div className="flex items-center justify-center h-40">
          <div className="flex items-center gap-3 text-gray-500 dark:text-gray-400">
            <svg className="animate-spin h-5 w-5" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            Loading…
          </div>
        </div>
      ) : (
        <>
          <TransactionTable
            transactions={transactions}
            categories={categories}
            onCategoryUpdated={handleCategoryUpdated}
            onBulkCategoryUpdated={handleBulkCategoryUpdated}
          />

          {totalPages > 1 && (
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-500 dark:text-gray-400">
                {(page - 1) * PAGE_SIZE + 1}–{Math.min(page * PAGE_SIZE, total)} of {total} transactions
              </span>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setPage(p => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className="px-3 py-1.5 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 disabled:opacity-40 rounded-md transition-colors"
                >
                  ← Prev
                </button>
                <span className="text-gray-600 dark:text-gray-400 px-2">
                  {page} / {totalPages}
                </span>
                <button
                  onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                  disabled={page === totalPages}
                  className="px-3 py-1.5 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 disabled:opacity-40 rounded-md transition-colors"
                >
                  Next →
                </button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  )
}
