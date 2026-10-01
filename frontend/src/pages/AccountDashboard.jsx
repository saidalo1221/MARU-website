import { useEffect, useState } from 'react'
import { Link, Navigate } from 'react-router-dom'
import { listAddresses } from '../api/addresses'
import { listMyOrders } from '../api/orders'
import { getWishlist } from '../api/wishlist'
import AccountNav from '../components/account/AccountNav'
import LoyaltyCard from '../components/account/LoyaltyCard'
import PushCard from '../components/account/PushCard'
import Seo from '../components/Seo'
import { useAuth } from '../context/AuthContext'
import { useLocale } from '../context/LocaleContext'
import { formatDate } from '../lib/format'

// Account dashboard (PRD ТЗ№2 §27): recent orders with status, plus shortcuts to
// the wishlist, addresses and profile.
export default function AccountDashboard() {
  const { t } = useLocale()
  const { user, loading: authLoading } = useAuth()
  const [orders, setOrders] = useState(null)
  const [wishlistCount, setWishlistCount] = useState(null)
  const [addressCount, setAddressCount] = useState(null)

  useEffect(() => {
    if (!user) return
    listMyOrders().then(({ data }) => setOrders(data)).catch(() => setOrders([]))
    getWishlist().then((items) => setWishlistCount(items.length)).catch(() => setWishlistCount(0))
    listAddresses().then((items) => setAddressCount(items.length)).catch(() => setAddressCount(0))
  }, [user])

  if (authLoading) return null
  if (!user) return <Navigate to="/login" replace />

  const recent = (orders || []).slice(0, 3)
  const name = user.first_name || user.email

  return (
    <div className="max-w-3xl mx-auto px-4 py-8">
      <Seo title={t('dashboard.title')} noindex />
      <AccountNav />
      <h1 className="text-2xl font-bold mb-1">{t('dashboard.title')}</h1>
      <p className="text-gray-500 mb-6">{t('dashboard.welcome', { name })}</p>

      <LoyaltyCard />
      <PushCard />

      <section className="border border-gray-200 rounded-lg p-4 mb-6" aria-labelledby="recent-orders">
        <div className="flex items-center justify-between mb-3">
          <h2 id="recent-orders" className="font-semibold">{t('dashboard.recentOrders')}</h2>
          <Link to="/account/orders" className="text-sm text-brand underline">{t('dashboard.viewAll')}</Link>
        </div>
        {orders === null && <p className="text-sm text-gray-500">{t('dashboard.loading')}</p>}
        {orders !== null && recent.length === 0 && (
          <div className="text-sm text-gray-500">
            <p>{t('dashboard.noOrders')}</p>
            <Link to="/shop" className="inline-block mt-2 text-brand underline">{t('dashboard.startShopping')}</Link>
          </div>
        )}
        <ul className="divide-y divide-gray-100">
          {recent.map((order) => (
            <li key={order.id}>
              <Link to={`/orders/${order.id}`} className="flex flex-wrap justify-between gap-2 py-2 text-sm">
                <span>
                  <span className="font-medium">{order.order_number}</span>
                  <span className="text-gray-500"> — {formatDate(order.created_at)}</span>
                </span>
                <span>
                  {t(`orderStatus.statusLabels.${order.status}`)} · {order.currency} {Number(order.total_amount).toFixed(2)}
                </span>
              </Link>
            </li>
          ))}
        </ul>
      </section>

      <ul className="grid sm:grid-cols-3 gap-3 text-sm">
        <li className="border border-gray-200 rounded-lg p-4">
          <Link to="/account/wishlist" className="font-medium text-brand underline">{t('wishlist.title')}</Link>
          <p className="text-gray-500 mt-1">{wishlistCount === null ? '…' : t('dashboard.wishlistCount', { n: wishlistCount })}</p>
        </li>
        <li className="border border-gray-200 rounded-lg p-4">
          <Link to="/account/addresses" className="font-medium text-brand underline">{t('addresses.title')}</Link>
          <p className="text-gray-500 mt-1">{addressCount === null ? '…' : t('dashboard.addressCount', { n: addressCount })}</p>
        </li>
        <li className="border border-gray-200 rounded-lg p-4">
          <Link to="/account/profile" className="font-medium text-brand underline">{t('header.profile')}</Link>
          <p className="text-gray-500 mt-1">{t('dashboard.settings')}</p>
        </li>
      </ul>
    </div>
  )
}
