import { Link } from 'react-router-dom'
import { useEffect, useRef, useState } from 'react'
import { useAuth } from '../../context/AuthContext'
import { useCart } from '../../context/CartContext'
import { useLocale } from '../../context/LocaleContext'
import { aboutGroups, businessGroups, shopGroups, supportGroups } from '../../lib/navLinks'
import SearchBar from '../SearchBar'
import CountrySwitcher from '../CountrySwitcher'
import CurrencySwitcher from '../CurrencySwitcher'
import LanguageSwitcher from '../LanguageSwitcher'
import ThemeSwitcher from '../ThemeSwitcher'
import MobileMenu from './MobileMenu'
import NavMenu from './NavMenu'

const navLink = 'whitespace-nowrap rounded-full px-3 py-1.5 transition-colors hover:bg-gray-100'

// Full-width, flat navbar that stays pinned below a static info strip. Once the page has scrolled
// a shadow appears, so the bar reads as sitting above the content (state feedback, no scroll listener).
export default function Header() {
  const { user, logout } = useAuth()
  const { cart } = useCart()
  const { t } = useLocale()
  const [menuOpen, setMenuOpen] = useState(false)
  const [scrolled, setScrolled] = useState(false)
  const sentinelRef = useRef(null)
  const itemCount = cart?.item_count ?? 0

  useEffect(() => {
    const el = sentinelRef.current
    if (!el || typeof IntersectionObserver === 'undefined') return undefined
    const io = new IntersectionObserver(([entry]) => setScrolled(!entry.isIntersecting))
    io.observe(el)
    return () => io.disconnect()
  }, [])

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

  const cartBadge = itemCount > 0 && (
    <span className="ml-1.5 rounded-full bg-brand px-1.5 py-0.5 text-xs leading-none text-white">{itemCount}</span>
  )

  return (
    <>
      {/* Top information bar (PRD ТЗ№2 §5): delivery, business offer, and the country / language / currency choice. */}
      <div className="hidden md:block bg-brand-light text-xs text-gray-700">
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-x-6 px-6 py-2">
          <Link to="/delivery" className="font-medium hover:underline">{t('header.topBarDelivery')}</Link>
          <div className="flex items-center gap-3">
            <Link to="/wholesale" className="mr-2 whitespace-nowrap rounded-full bg-brand px-3 py-1 font-medium text-white transition-colors hover:bg-brand-dark">
              {t('header.topBarBusiness')}
            </Link>
            <ThemeSwitcher />
            <CountrySwitcher />
            <LanguageSwitcher />
            <CurrencySwitcher />
          </div>
        </div>
      </div>

      <div ref={sentinelRef} aria-hidden="true" className="h-px" />

      <header
        className={`sticky top-0 z-40 -mt-px border-b border-gray-200 bg-page/95 backdrop-blur transition-shadow ${
          scrolled ? 'shadow-token' : ''
        }`}
      >
        {/* Mobile: row 1 logo | actions, row 2 full-width search. */}
        <div className="mx-auto flex max-w-7xl flex-wrap items-center gap-x-2 gap-y-2 px-4 py-3 md:hidden">
          <Link to="/" className="mr-auto text-lg font-bold text-brand">MARU</Link>
          <Link to="/account/wishlist" className="px-2 text-lg" aria-label={t('header.wishlist')}>
            ♡
          </Link>
          <Link to="/cart" className="relative flex items-center rounded-full border border-gray-200 px-3 py-1 text-sm">
            {t('header.cart')}
            {cartBadge}
          </Link>
          <button onClick={() => setMenuOpen(true)} aria-label={t('header.openMenu')} className="px-2 text-xl">
            ☰
          </button>
          <div className="basis-full min-w-0">
            <SearchBar />
          </div>
        </div>

        {/* Desktop: one line, 64px. */}
        <div className="mx-auto hidden max-w-7xl items-center gap-x-4 px-6 py-2.5 md:flex">
          <Link to="/" className="text-xl font-bold text-brand">MARU</Link>
          <nav aria-label={t('header.mainNav')} className="flex items-center text-sm font-medium">
            <NavMenu label={t('header.shop')} groups={shopGroups(t)} />
            <NavMenu label={t('header.navBusiness')} groups={businessGroups(t)} />
            <NavMenu label={t('header.navAbout')} groups={aboutGroups(t)} />
            <NavMenu label={t('header.navSupport')} groups={supportGroups(t)} />
            <Link to="/blog" className={navLink}>{t('footer.blog')}</Link>
          </nav>
          <div className="min-w-[10rem] max-w-md flex-1">
            <SearchBar />
          </div>
          <div className="flex items-center gap-1 text-sm font-medium">
            {user ? (
              <NavMenu label={user.first_name || t('header.account')} groups={[{ items: accountItems }]} align="right" />
            ) : (
              <Link to="/login" className="whitespace-nowrap rounded-full px-4 py-1.5 text-brand transition-colors hover:bg-brand-light">
                {t('header.login')}
              </Link>
            )}
            <Link to="/account/wishlist" className="rounded-full px-2.5 py-1 text-lg transition-colors hover:bg-gray-100" aria-label={t('header.wishlist')}>
              ♡
            </Link>
            <Link to="/cart" className="flex items-center whitespace-nowrap rounded-full bg-brand px-4 py-1.5 text-white transition-colors hover:bg-brand-dark">
              {t('header.cart')}
              {itemCount > 0 && (
                <span className="ml-1.5 rounded-full bg-white/95 px-1.5 py-0.5 text-xs leading-none !text-ink">{itemCount}</span>
              )}
            </Link>
          </div>
        </div>
      </header>

      <MobileMenu open={menuOpen} onClose={() => setMenuOpen(false)} />
    </>
  )
}
