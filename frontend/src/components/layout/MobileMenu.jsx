import { useEffect, useRef } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import { useLocale } from '../../context/LocaleContext'
import LanguageSwitcher from '../LanguageSwitcher'
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

  return (
    <div ref={dialogRef} className="fixed inset-0 z-50 bg-white flex flex-col" role="dialog" aria-modal="true" aria-label={t('mobileMenu.title')}>
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200">
        <span className="font-bold text-brand">MARU</span>
        <button onClick={onClose} aria-label={t('mobileMenu.closeMenu')} className="text-xl">✕</button>
      </div>
      <nav aria-label={t('mobileMenu.title')} className="flex-1 overflow-y-auto px-4 py-2" onClick={onClose}>
        <Link to="/shop" className={linkClass}>{t('header.shop')}</Link>
        <Link to="/b2b" className={linkClass}>{t('footer.b2b')}</Link>
        <Link to="/wholesale" className={linkClass}>{t('footer.wholesale')}</Link>
        <Link to="/distributor" className={linkClass}>{t('footer.distributor')}</Link>
        <Link to="/quote" className={linkClass}>{t('footer.requestQuote')}</Link>
        <Link to="/about" className={linkClass}>{t('footer.about')}</Link>
        <Link to="/contact" className={linkClass}>{t('footer.contact')}</Link>
        <Link to="/delivery" className={linkClass}>{t('footer.delivery')}</Link>
        <Link to="/payment" className={linkClass}>{t('footer.payment')}</Link>
        <Link to="/returns" className={linkClass}>{t('footer.returns')}</Link>
        <Link to="/faq" className={linkClass}>{t('footer.faq')}</Link>
        {user ? (
          <>
            {user.role !== 'customer' && (
              <Link to="/admin" className={linkClass}>{t('header.admin')}</Link>
            )}
            <Link to="/account/orders" className={linkClass}>{t('mobileMenu.myOrders')}</Link>
            <Link to="/account/wishlist" className={linkClass}>{t('wishlist.title')}</Link>
            <Link to="/account/addresses" className={linkClass}>{t('addresses.title')}</Link>
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
        <div className="flex items-center gap-3 py-4">
          <DarkModeToggle />
          <LanguageSwitcher />
          <CurrencySwitcher />
        </div>
      </nav>
    </div>
  )
}
