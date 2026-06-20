import { formatCurrency } from '../utils/formatters.js'

function Card({ title, value, color, subtitle }) {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
      <p className="text-sm font-medium text-gray-500 dark:text-gray-400">{title}</p>
      <p className={`text-3xl font-bold mt-1 ${color}`}>{formatCurrency(value)}</p>
      {subtitle && <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">{subtitle}</p>}
    </div>
  )
}

export default function Summary({ stats }) {
  if (!stats) return null
  const { total_income, total_expenses, net } = stats
  return (
    <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
      <Card title="Total Income" value={total_income} color="text-green-600 dark:text-green-400" />
      <Card title="Total Expenses" value={total_expenses} color="text-red-600 dark:text-red-400" />
      <Card
        title="Net"
        value={net}
        color={Number(net) >= 0 ? 'text-blue-600 dark:text-blue-400' : 'text-orange-600 dark:text-orange-400'}
      />
    </div>
  )
}
