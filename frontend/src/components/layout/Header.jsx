import { Link } from 'react-router-dom'
import { useState } from 'react'
import { useAuth } from '../../context/AuthContext'
import { useCart } from '../../context/CartContext'
import { useLocale } from '../../context/LocaleContext'
import SearchBar from '../SearchBar'
import CurrencySwitcher from '../CurrencySwitcher'
import LanguageSwitcher from '../LanguageSwitcher'
import DarkModeToggle from '../DarkModeToggle'
import MobileMenu from './MobileMenu'

export default function Header() {
  const { user, logout } = useAuth()
  const { cart } = useCart()
  const { t } = useLocale()
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
        <DarkModeToggle />
        <Link to="/account/wishlist" className="px-2 text-lg" aria-label={t('header.wishlist')}>
          ♡
        </Link>
        <Link to="/cart" className="relative px-2" aria-label={t('header.cart')}>
          🛒
          {itemCount > 0 && (
            <span className="absolute -top-1 -right-1 bg-brand text-white text-[10px] rounded-full w-4 h-4 flex items-center justify-center">
              {itemCount}
            </span>
          )}
        </Link>
        <button onClick={() => setMenuOpen(true)} aria-label={t('header.openMenu')} className="px-2 text-xl">
          ☰
        </button>
      </div>

      {/* Desktop header */}
      <div className="hidden md:flex items-center gap-6 px-6 py-3 max-w-7xl mx-auto">
        <Link to="/" className="font-bold text-xl text-brand">MARU</Link>
        <nav className="flex items-center gap-4 text-sm font-medium">
          <Link to="/shop">{t('header.shop')}</Link>
          <Link to="/account/orders">{t('header.orders')}</Link>
          <Link to="/account/addresses">{t('header.addresses')}</Link>
        </nav>
        <div className="flex-1 max-w-md">
          <SearchBar />
        </div>
        <div className="flex items-center gap-3">
          <DarkModeToggle />
          <LanguageSwitcher />
          <CurrencySwitcher />
          {user ? (
            <>
              {user.role !== 'customer' && (
                <Link to="/admin" className="text-sm font-medium text-gray-700">
                  {t('header.admin')}
                </Link>
              )}
              <Link to="/account/orders" className="text-sm">
                {user.first_name || t('header.account')}
              </Link>
              <button onClick={logout} className="text-sm text-gray-500 hover:text-gray-800">
                {t('header.logout')}
              </button>
            </>
          ) : (
            <Link to="/login" className="text-sm font-medium text-brand">
              {t('header.login')}
            </Link>
          )}
          <Link to="/account/wishlist" className="text-lg" aria-label={t('header.wishlist')}>
            ♡
          </Link>
          <Link to="/cart" className="relative text-sm">
            {t('header.cart')}
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
