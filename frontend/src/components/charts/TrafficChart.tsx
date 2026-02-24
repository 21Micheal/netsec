import { useEffect, useState } from 'react'
import {
  LineChart, Line, XAxis, YAxis, Tooltip,
  ResponsiveContainer, CartesianGrid
} from 'recharts'
import SocketService from '../../services/socket'

export default function TrafficChart() {
  const [data, setData] = useState<{ name: string; traffic: number }[]>([])
  const socket = SocketService.connect()

  useEffect(() => {
    const handleTraffic = (update: { name: string; traffic: number }) => {
      setData(prev => [...prev.slice(-11), update]) // keep last 12 points
    }

    socket.on('traffic_update', handleTraffic)
    return () => { socket.off('traffic_update', handleTraffic) }
  }, [socket])

  return (
    <div className="w-full h-64">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
          <XAxis dataKey="name" stroke="#9ca3af" />
          <YAxis stroke="#9ca3af" />
          <Tooltip
            contentStyle={{
              backgroundColor: '#111827',
              border: '1px solid #1f2937',
              color: '#e5e7eb',
            }}
          />
          <Line
            type="monotone"
            dataKey="traffic"
            stroke="#3b82f6"
            strokeWidth={2}
            dot={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
