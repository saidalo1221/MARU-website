import { Link } from 'react-router-dom'
import { useState } from 'react'
import { useAuth } from '../../context/AuthContext'
import { useCart } from '../../context/CartContext'
import { useLocale } from '../../context/LocaleContext'
import { aboutGroups, businessGroups, shopGroups, supportGroups } from '../../lib/navLinks'
import SearchBar from '../SearchBar'
import CountrySwitcher from '../CountrySwitcher'
import CurrencySwitcher from '../CurrencySwitcher'
import LanguageSwitcher from '../LanguageSwitcher'
import DarkModeToggle from '../DarkModeToggle'
import MobileMenu from './MobileMenu'
import NavMenu from './NavMenu'

export default function Header() {
  const { user, logout } = useAuth()
  const { cart } = useCart()
  const { t } = useLocale()
  const [menuOpen, setMenuOpen] = useState(false)
  const itemCount = cart?.item_count ?? 0

  const accountItems = user
    ? [
        { to: '/account', label: t('header.dashboard') },
        { to: '/account/orders', label: t('header.orders') },
        { to: '/account/wishlist', label: t('header.wishlist') },
        { to: '/account/addresses', label: t('header.addresses') },
        { to: '/account/profile', label: t('header.profile') },
        ...(user.role !== 'customer' ? [{ to: '/admin', label: t('header.admin') }] : []),
        { label: t('header.logout'), onClick: logout },
      ]
    : []

  return (
    <header className="border-b border-gray-200 sticky top-0 bg-white z-40">
      {/* Top information bar (PRD ТЗ№2 §5): delivery and business offers. */}
      <div className="hidden md:block bg-gray-50 border-b border-gray-200 text-xs text-gray-600">
        <div className="max-w-7xl mx-auto px-6 py-1.5 flex flex-wrap items-center justify-between gap-x-6 gap-y-1">
          <Link to="/delivery" className="hover:underline">{t('header.topBarDelivery')}</Link>
          <Link to="/wholesale" className="hover:underline">{t('header.topBarBusiness')}</Link>
        </div>
      </div>

      {/* Mobile header: row 1 Logo | actions, row 2 full-width Search — six
          items plus a search box don't fit one row at phone widths. */}
      <div className="flex flex-wrap items-center gap-x-2 gap-y-2 px-4 py-3 md:hidden">
        <Link to="/" className="font-bold text-lg text-brand mr-auto">MARU</Link>
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
        <div className="basis-full min-w-0">
          <SearchBar />
        </div>
      </div>

      {/* Desktop header */}
      <div className="hidden md:flex flex-wrap items-center gap-x-6 gap-y-2 px-6 py-3 max-w-7xl mx-auto">
        <Link to="/" className="font-bold text-xl text-brand">MARU</Link>
        <nav aria-label={t('header.mainNav')} className="flex flex-wrap items-center gap-x-4 gap-y-1 text-sm font-medium">
          <NavMenu label={t('header.shop')} groups={shopGroups(t)} />
          <NavMenu label={t('header.navBusiness')} groups={businessGroups(t)} />
          <NavMenu label={t('header.navAbout')} groups={aboutGroups(t)} />
          <NavMenu label={t('header.navSupport')} groups={supportGroups(t)} />
          <Link to="/blog">{t('footer.blog')}</Link>
        </nav>
        <div className="flex-1 min-w-[10rem] max-w-md">
          <SearchBar />
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <DarkModeToggle />
          <CountrySwitcher />
          <LanguageSwitcher />
          <CurrencySwitcher />
          {user ? (
            <div className="text-sm font-medium">
              <NavMenu label={user.first_name || t('header.account')} groups={[{ items: accountItems }]} align="right" />
            </div>
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
