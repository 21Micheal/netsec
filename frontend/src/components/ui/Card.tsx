import { ReactNode } from 'react'

interface CardProps {
  title?: string
  children: ReactNode
}

export default function Card({ title, children }: CardProps) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-2xl p-4 shadow-md">
      {title && <h3 className="text-lg font-semibold mb-3 text-blue-400">{title}</h3>}
      {children}
    </div>
  )
}
