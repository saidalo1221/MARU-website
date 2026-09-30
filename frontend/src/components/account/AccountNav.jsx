import { NavLink } from 'react-router-dom'
import { useLocale } from '../../context/LocaleContext'

const linkClass = ({ isActive }) =>
  `pb-2 border-b-2 text-sm font-medium ${isActive ? 'border-brand text-brand' : 'border-transparent text-gray-500'}`

export default function AccountNav() {
  const { t } = useLocale()
  return (
    <nav aria-label={t('header.account')} className="flex gap-6 mb-6 border-b border-gray-200">
      <NavLink to="/account/orders" className={linkClass}>{t('footer.orders')}</NavLink>
      <NavLink to="/account/wishlist" className={linkClass}>{t('wishlist.title')}</NavLink>
      <NavLink to="/account/addresses" className={linkClass}>{t('addresses.title')}</NavLink>
      <NavLink to="/account/privacy" className={linkClass}>{t('privacy.title')}</NavLink>
    </nav>
  )
}
