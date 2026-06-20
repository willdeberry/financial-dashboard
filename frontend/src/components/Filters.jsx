import { useState } from 'react'

const SOURCE_LABELS = { bank: 'Bank', credit_card: 'Credit Card', payroll: 'Payroll' }

export default function Filters({ categories, onFilter }) {
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const [selectedCategories, setSelectedCategories] = useState([])
  const [sources, setSources] = useState([])
  const [search, setSearch] = useState('')
  const [minAmount, setMinAmount] = useState('')
  const [maxAmount, setMaxAmount] = useState('')

  const toggleSet = (setter, value) =>
    setter(prev => prev.includes(value) ? prev.filter(v => v !== value) : [...prev, value])

  const apply = () =>
    onFilter({
      start_date: startDate || undefined,
      end_date: endDate || undefined,
      category_ids: selectedCategories.length ? selectedCategories.join(',') : undefined,
      sources: sources.length ? sources.join(',') : undefined,
      search: search || undefined,
      min_amount: minAmount || undefined,
      max_amount: maxAmount || undefined,
    })

  const reset = () => {
    setStartDate(''); setEndDate(''); setSelectedCategories([])
    setSources([]); setSearch(''); setMinAmount(''); setMaxAmount('')
    onFilter({})
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-5">
      <h3 className="font-semibold text-gray-900 dark:text-white mb-4">Filters</h3>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-4">
        {[
          ['Start Date', 'date', startDate, setStartDate],
          ['End Date', 'date', endDate, setEndDate],
          ['Min Amount ($)', 'number', minAmount, setMinAmount],
          ['Max Amount ($)', 'number', maxAmount, setMaxAmount],
        ].map(([label, type, val, set]) => (
          <div key={label}>
            <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">{label}</label>
            <input
              type={type}
              value={val}
              onChange={e => set(e.target.value)}
              placeholder={type === 'number' ? '0.00' : undefined}
              className="w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        ))}
      </div>

      <div className="mb-4">
        <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">Search payee or description</label>
        <input
          type="text"
          value={search}
          onChange={e => setSearch(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && apply()}
          placeholder="Search..."
          className="w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      <div className="mb-4">
        <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-2">Source</label>
        <div className="flex gap-4">
          {Object.entries(SOURCE_LABELS).map(([val, label]) => (
            <label key={val} className="flex items-center gap-2 cursor-pointer select-none">
              <input
                type="checkbox"
                checked={sources.includes(val)}
                onChange={() => toggleSet(setSources, val)}
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              <span className="text-sm text-gray-700 dark:text-gray-300">{label}</span>
            </label>
          ))}
        </div>
      </div>

      {categories.length > 0 && (
        <div className="mb-4">
          <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-2">Categories</label>
          <div className="flex flex-wrap gap-2">
            <button
              onClick={() => toggleSet(setSelectedCategories, 0)}
              className={`px-3 py-1 rounded-full text-xs font-medium transition-all border ${
                selectedCategories.includes(0)
                  ? 'bg-gray-500 text-white border-transparent shadow-sm'
                  : 'text-gray-600 dark:text-gray-400 bg-gray-100 dark:bg-gray-700 border-gray-200 dark:border-gray-600 hover:bg-gray-200 dark:hover:bg-gray-600'
              }`}
            >
              Uncategorized
            </button>
            {categories.map(cat => {
              const selected = selectedCategories.includes(cat.id)
              return (
                <button
                  key={cat.id}
                  onClick={() => toggleSet(setSelectedCategories, cat.id)}
                  className={`px-3 py-1 rounded-full text-xs font-medium transition-all border ${
                    selected
                      ? 'text-white border-transparent shadow-sm'
                      : 'text-gray-600 dark:text-gray-400 bg-gray-100 dark:bg-gray-700 border-gray-200 dark:border-gray-600 hover:bg-gray-200 dark:hover:bg-gray-600'
                  }`}
                  style={selected ? { backgroundColor: cat.color || '#3b82f6' } : {}}
                >
                  {cat.name}
                </button>
              )
            })}
          </div>
        </div>
      )}

      <div className="flex gap-2">
        <button
          onClick={apply}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-md transition-colors"
        >
          Apply
        </button>
        <button
          onClick={reset}
          className="px-4 py-2 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 text-sm font-medium rounded-md transition-colors"
        >
          Reset
        </button>
      </div>
    </div>
  )
}
