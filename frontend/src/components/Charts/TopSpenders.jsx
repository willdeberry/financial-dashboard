import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import { formatCurrency } from '../../utils/formatters.js'

export default function TopSpenders({ data }) {
  if (!data?.length) {
    return <div className="flex items-center justify-center h-64 text-gray-400 text-sm">No spending data yet</div>
  }

  const chartData = data.slice(0, 8).map(d => ({
    name: d.category_name,
    amount: Number(d.total),
    color: d.color || '#6b7280',
  }))

  return (
    <ResponsiveContainer width="100%" height={260}>
      <BarChart data={chartData} layout="vertical" margin={{ top: 5, right: 30, left: 90, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="currentColor" className="text-gray-200 dark:text-gray-700" opacity={0.5} horizontal={false} />
        <XAxis type="number" tickFormatter={v => `$${v >= 1000 ? (v / 1000).toFixed(0) + 'k' : v}`} tick={{ fontSize: 11 }} tickLine={false} axisLine={false} />
        <YAxis type="category" dataKey="name" tick={{ fontSize: 11 }} tickLine={false} axisLine={false} width={85} />
        <Tooltip formatter={v => formatCurrency(v)} />
        <Bar dataKey="amount" radius={[0, 4, 4, 0]} maxBarSize={28}>
          {chartData.map((entry, i) => (
            <Cell key={i} fill={entry.color} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}
