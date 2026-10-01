import { useEffect, useRef } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import { useLocale } from '../../context/LocaleContext'
import { VOLUMES_ML, aboutGroups, businessGroups, supportGroups } from '../../lib/navLinks'
import LanguageSwitcher from '../LanguageSwitcher'
import CountrySwitcher from '../CountrySwitcher'
import CurrencySwitcher from '../CurrencySwitcher'
import DarkModeToggle from '../DarkModeToggle'
import useDialogFocus from '../../lib/useDialogFocus'

export default function MobileMenu({ open, onClose }) {
  const { user, logout } = useAuth()
  const { t } = useLocale()
  const dialogRef = useRef(null)
  useDialogFocus(dialogRef, open)

  useEffect(() => {
    if (!open) return undefined
    const onKey = (e) => e.key === 'Escape' && onClose()
    document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  }, [open, onClose])

  if (!open) return null

  const linkClass = 'block py-3 border-b border-gray-100 text-base'
  const headingClass = 'pt-4 pb-1 text-xs font-semibold uppercase tracking-wide text-gray-500'
  const flat = (groups) => groups.flatMap((g) => g.items)

  // Order follows PRD ТЗ№2 §6: Shop, Categories, Business, About, Support,
  // Blog, Account, Language, Currency, Country.
  return (
    <div ref={dialogRef} className="fixed inset-0 z-50 bg-white flex flex-col" role="dialog" aria-modal="true" aria-label={t('mobileMenu.title')}>
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200">
        <span className="font-bold text-brand">MARU</span>
        <button onClick={onClose} aria-label={t('mobileMenu.closeMenu')} className="text-xl">✕</button>
      </div>
      <nav aria-label={t('mobileMenu.title')} className="flex-1 overflow-y-auto px-4 py-2" onClick={onClose}>
        <Link to="/shop" className={linkClass}>{t('header.shop')}</Link>
        <Link to="/shop?sort=newest" className={linkClass}>{t('header.newFeatured')}</Link>

        <p className={headingClass}>{t('mobileMenu.categories')}</p>
        {VOLUMES_ML.map((ml) => (
          <Link key={ml} to={`/shop?capacity=${ml}`} className={linkClass}>{t('catalog.ml', { n: ml })}</Link>
        ))}

        <p className={headingClass}>{t('header.navBusiness')}</p>
        {flat(businessGroups(t)).map((i) => <Link key={i.to} to={i.to} className={linkClass}>{i.label}</Link>)}

        <p className={headingClass}>{t('header.navAbout')}</p>
        {flat(aboutGroups(t)).map((i) => <Link key={i.to} to={i.to} className={linkClass}>{i.label}</Link>)}

        <p className={headingClass}>{t('header.navSupport')}</p>
        {flat(supportGroups(t)).map((i) => <Link key={i.to} to={i.to} className={linkClass}>{i.label}</Link>)}

        <Link to="/blog" className={`${linkClass} mt-2`}>{t('footer.blog')}</Link>

        <p className={headingClass}>{t('header.account')}</p>
        {user ? (
          <>
            {user.role !== 'customer' && (
              <Link to="/admin" className={linkClass}>{t('header.admin')}</Link>
            )}
            <Link to="/account" className={linkClass}>{t('header.dashboard')}</Link>
            <Link to="/account/orders" className={linkClass}>{t('mobileMenu.myOrders')}</Link>
            <Link to="/account/wishlist" className={linkClass}>{t('wishlist.title')}</Link>
            <Link to="/account/addresses" className={linkClass}>{t('addresses.title')}</Link>
            <Link to="/account/profile" className={linkClass}>{t('header.profile')}</Link>
            <button
              onClick={logout}
              className={`${linkClass} text-left w-full text-red-600`}
            >
              {t('mobileMenu.logout')}
            </button>
          </>
        ) : (
          <>
            <Link to="/login" className={linkClass}>{t('header.login')}</Link>
            <Link to="/register" className={linkClass}>{t('mobileMenu.register')}</Link>
          </>
        )}

        {/* Settings must not close the menu on every change. */}
        <div className="flex flex-wrap items-center gap-3 py-4" onClick={(e) => e.stopPropagation()}>
          <DarkModeToggle />
          <LanguageSwitcher />
          <CurrencySwitcher />
          <CountrySwitcher />
        </div>
      </nav>
    </div>
  )
}
