import { useEffect, useState } from 'react'
import {
  BarChart, Bar, XAxis, YAxis, Tooltip,
  ResponsiveContainer, CartesianGrid
} from 'recharts'
import SocketService from '../../services/socket'

export default function ScanStatsChart() {
  const [data, setData] = useState<{ day: string; scans: number }[]>([])

  useEffect(() => {
    const socket = SocketService.connect()

    const handleScan = (update: { day: string; scans: number }) => {
      setData(prev => {
        const existing = prev.find(d => d.day === update.day)
        if (existing) {
          // update existing day's scans
          return prev.map(d => (d.day === update.day ? update : d))
        }
        return [...prev.slice(-6), update] // keep 7 days
      })
    }

    socket.on('scan_update', handleScan)

    return () => {
      socket.off('scan_update', handleScan)
    }
  }, []) // Empty dependency array

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