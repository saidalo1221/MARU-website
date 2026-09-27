import { Link } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import LanguageSwitcher from '../LanguageSwitcher'
import CurrencySwitcher from '../CurrencySwitcher'

export default function MobileMenu({ open, onClose }) {
  const { user, logout } = useAuth()

  if (!open) return null

  const linkClass = 'block py-3 border-b border-gray-100 text-base'

  return (
    <div className="fixed inset-0 z-50 bg-white flex flex-col">
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200">
        <span className="font-bold text-brand">MARU</span>
        <button onClick={onClose} aria-label="Close menu" className="text-xl">✕</button>
      </div>
      <nav className="flex-1 overflow-y-auto px-4 py-2" onClick={onClose}>
        <Link to="/shop" className={linkClass}>Shop</Link>
        {user ? (
          <>
            <Link to="/account/orders" className={linkClass}>My Orders</Link>
            <button
              onClick={logout}
              className={`${linkClass} text-left w-full text-red-600`}
            >
              Log out
            </button>
          </>
        ) : (
          <>
            <Link to="/login" className={linkClass}>Login</Link>
            <Link to="/register" className={linkClass}>Register</Link>
          </>
        )}
        <div className="flex items-center gap-3 py-4">
          <LanguageSwitcher />
          <CurrencySwitcher />
        </div>
      </nav>
    </div>
  )
}
