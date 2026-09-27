import { Link } from 'react-router-dom'
import { useState } from 'react'
import { useAuth } from '../../context/AuthContext'
import { useCart } from '../../context/CartContext'
import SearchBar from '../SearchBar'
import CurrencySwitcher from '../CurrencySwitcher'
import LanguageSwitcher from '../LanguageSwitcher'
import MobileMenu from './MobileMenu'

export default function Header() {
  const { user } = useAuth()
  const { cart } = useCart()
  const [menuOpen, setMenuOpen] = useState(false)
  const itemCount = cart?.item_count ?? 0

  return (
    <header className="border-b border-gray-200 sticky top-0 bg-white z-40">
      {/* Mobile header: Logo | Search | Cart | Menu */}
      <div className="flex items-center gap-2 px-4 py-3 md:hidden">
        <Link to="/" className="font-bold text-lg text-brand">MARU</Link>
        <div className="flex-1">
          <SearchBar />
        </div>
        <Link to="/cart" className="relative px-2" aria-label="Cart">
          🛒
          {itemCount > 0 && (
            <span className="absolute -top-1 -right-1 bg-brand text-white text-[10px] rounded-full w-4 h-4 flex items-center justify-center">
              {itemCount}
            </span>
          )}
        </Link>
        <button onClick={() => setMenuOpen(true)} aria-label="Open menu" className="px-2 text-xl">
          ☰
        </button>
      </div>

      {/* Desktop header */}
      <div className="hidden md:flex items-center gap-6 px-6 py-3 max-w-7xl mx-auto">
        <Link to="/" className="font-bold text-xl text-brand">MARU</Link>
        <nav className="flex items-center gap-4 text-sm font-medium">
          <Link to="/shop">Shop</Link>
        </nav>
        <div className="flex-1 max-w-md">
          <SearchBar />
        </div>
        <div className="flex items-center gap-3">
          <LanguageSwitcher />
          <CurrencySwitcher />
          <Link to={user ? '/account/orders' : '/login'} className="text-sm">
            {user ? user.first_name || 'Account' : 'Login'}
          </Link>
          <Link to="/cart" className="relative text-sm">
            Cart
            {itemCount > 0 && (
              <span className="ml-1 bg-brand text-white text-xs rounded-full px-1.5">
                {itemCount}
              </span>
            )}
          </Link>
        </div>
      </div>

      <MobileMenu open={menuOpen} onClose={() => setMenuOpen(false)} />
    </header>
  )
}
