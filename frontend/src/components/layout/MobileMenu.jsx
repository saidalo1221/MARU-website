import { Link } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import { useLocale } from '../../context/LocaleContext'
import LanguageSwitcher from '../LanguageSwitcher'
import CurrencySwitcher from '../CurrencySwitcher'

export default function MobileMenu({ open, onClose }) {
  const { user, logout } = useAuth()
  const { t } = useLocale()

  if (!open) return null

  const linkClass = 'block py-3 border-b border-gray-100 text-base'

  return (
    <div className="fixed inset-0 z-50 bg-white flex flex-col">
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200">
        <span className="font-bold text-brand">MARU</span>
        <button onClick={onClose} aria-label={t('mobileMenu.closeMenu')} className="text-xl">✕</button>
      </div>
      <nav className="flex-1 overflow-y-auto px-4 py-2" onClick={onClose}>
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
          <LanguageSwitcher />
          <CurrencySwitcher />
        </div>
      </nav>
    </div>
  )
}
