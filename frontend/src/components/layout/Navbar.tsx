import { Link } from 'react-router-dom'

export default function Navbar() {
  return (
    <nav className="flex gap-6 p-4 bg-gray-900 border-b border-gray-800">
      <Link to="/" className="hover:text-blue-400">Dashboard</Link>
      <Link to="/vulnerabilities" className="hover:text-blue-400">Vulnerabilities</Link>
      <Link to="/risks" className="hover:text-blue-400">Risks</Link>
      <Link to="/settings" className="hover:text-blue-400">Settings</Link>
    </nav>
  )
}
