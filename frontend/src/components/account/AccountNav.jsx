import { NavLink } from 'react-router-dom'
import { useLocale } from '../../context/LocaleContext'

// Shared look for the account pages (panels, inputs, order status chip).
export const accountPanel = 'rounded-3xl border border-gray-200 bg-gray-50 p-5 md:p-6'
export const accountInput = 'w-full rounded-2xl border border-gray-300 bg-white px-4 py-2.5 text-sm'
export const statusPill = 'rounded-full bg-brand-light px-3 py-0.5 text-xs font-medium text-gray-800'

const linkClass = ({ isActive }) =>
  `whitespace-nowrap rounded-full px-4 py-2 text-sm font-medium transition-colors ${
    isActive ? 'bg-brand text-white' : 'text-gray-600 hover:bg-white'
  }`

export default function AccountNav() {
  const { t } = useLocale()
  return (
    <nav aria-label={t('header.account')} className="mb-8 flex w-fit max-w-full gap-1 overflow-x-auto rounded-full bg-gray-100 p-1">
      <NavLink to="/account" end className={linkClass}>{t('header.dashboard')}</NavLink>
      <NavLink to="/account/orders" className={linkClass}>{t('footer.orders')}</NavLink>
      <NavLink to="/account/wishlist" className={linkClass}>{t('wishlist.title')}</NavLink>
      <NavLink to="/account/addresses" className={linkClass}>{t('addresses.title')}</NavLink>
      <NavLink to="/account/profile" className={linkClass}>{t('header.profile')}</NavLink>
      <NavLink to="/account/privacy" className={linkClass}>{t('privacy.title')}</NavLink>
    </nav>
  )
}
