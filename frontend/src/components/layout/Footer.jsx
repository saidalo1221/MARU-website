import { Link } from 'react-router-dom'

export default function Footer() {
  return (
    <footer className="border-t border-gray-200 mt-12 py-8 px-4 text-sm text-gray-600">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row justify-between gap-4">
        <div>
          <p className="font-bold text-brand mb-1">MARU</p>
          <p>Plastic food containers, made in-house.</p>
        </div>
        <nav className="flex gap-6">
          <Link to="/shop">Shop</Link>
          <Link to="/cart">Cart</Link>
          <Link to="/account/orders">Orders</Link>
        </nav>
      </div>
      <p className="max-w-7xl mx-auto mt-6 text-xs text-gray-400">
        &copy; {new Date().getFullYear()} MARU
      </p>
    </footer>
  )
}
