import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { formatCurrency, MONTH_NAMES } from '../../utils/formatters.js'

export default function MonthlyTrend({ data }) {
  if (!data?.length) {
    return <div className="flex items-center justify-center h-64 text-gray-400 text-sm">No trend data yet</div>
  }

  const chartData = data.map(d => ({
    label: `${MONTH_NAMES[d.month - 1]} ${d.year}`,
    Income: Number(d.income),
    Expenses: Number(d.expenses),
    Net: Number(d.net),
  }))

  return (
    <ResponsiveContainer width="100%" height={280}>
      <LineChart data={chartData} margin={{ top: 5, right: 10, left: 10, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="currentColor" className="text-gray-200 dark:text-gray-700" opacity={0.5} />
        <XAxis dataKey="label" tick={{ fontSize: 11 }} tickLine={false} />
        <YAxis tickFormatter={v => `$${Math.abs(v) >= 1000 ? (v / 1000).toFixed(0) + 'k' : v}`} tick={{ fontSize: 11 }} tickLine={false} axisLine={false} />
        <Tooltip formatter={v => formatCurrency(v)} />
        <Legend iconType="circle" iconSize={8} />
        <Line type="monotone" dataKey="Income" stroke="#22c55e" strokeWidth={2} dot={false} />
        <Line type="monotone" dataKey="Expenses" stroke="#ef4444" strokeWidth={2} dot={false} />
        <Line type="monotone" dataKey="Net" stroke="#3b82f6" strokeWidth={2} dot={false} strokeDasharray="5 5" />
      </LineChart>
    </ResponsiveContainer>
  )
}
