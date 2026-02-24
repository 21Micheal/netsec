import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from 'recharts'

const data = [
  { day: 'Mon', scans: 14 },
  { day: 'Tue', scans: 22 },
  { day: 'Wed', scans: 10 },
  { day: 'Thu', scans: 18 },
  { day: 'Fri', scans: 25 },
  { day: 'Sat', scans: 9 },
  { day: 'Sun', scans: 11 },
]

export default function ScanStatsChart() {
  return (
    <div className="w-full h-64">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
          <XAxis dataKey="day" stroke="#9ca3af" />
          <YAxis stroke="#9ca3af" />
          <Tooltip
            contentStyle={{
              backgroundColor: '#111827',
              border: '1px solid #1f2937',
              color: '#e5e7eb',
            }}
          />
          <Bar dataKey="scans" fill="#10b981" radius={[6, 6, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
