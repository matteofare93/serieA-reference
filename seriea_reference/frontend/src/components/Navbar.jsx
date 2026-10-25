import { Link } from 'react-router-dom'

export default function Navbar() {
  return (
    <nav className="bg-blue-800 text-white shadow">
      <div className="max-w-screen-xl mx-auto px-4 py-3 flex items-center gap-6">
        <Link to="/" className="text-xl font-bold tracking-tight hover:text-blue-200">
          LegaBasket Serie A Reference
        </Link>
      </div>
    </nav>
  )
}
