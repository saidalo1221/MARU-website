import { useEffect, useState } from 'react'
import { Link, Navigate } from 'react-router-dom'
import { listAddresses } from '../api/addresses'
import { listMyOrders } from '../api/orders'
import { getWishlist } from '../api/wishlist'
import AccountNav, { accountPanel, statusPill } from '../components/account/AccountNav'
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

  const shortcuts = [
    { to: '/account/wishlist', title: t('wishlist.title'), text: wishlistCount === null ? '...' : t('dashboard.wishlistCount', { n: wishlistCount }) },
    { to: '/account/addresses', title: t('addresses.title'), text: addressCount === null ? '...' : t('dashboard.addressCount', { n: addressCount }) },
    { to: '/account/profile', title: t('header.profile'), text: t('dashboard.settings') },
  ]

  return (
    <div className="max-w-5xl mx-auto px-4 py-8 md:py-12">
      <Seo title={t('dashboard.title')} noindex />
      <AccountNav />

      <section className="mb-6 flex flex-wrap items-end justify-between gap-6 rounded-3xl bg-ink p-6 text-white md:p-10">
        <div>
          <h1 className="mb-2 text-3xl font-semibold tracking-tight md:text-5xl">{t('dashboard.title')}</h1>
          <p className="text-white/80">{t('dashboard.welcome', { name })}</p>
        </div>
        <Link to="/shop" className="rounded-full bg-brand px-7 py-3 font-semibold text-white transition hover:bg-brand-dark active:scale-[0.98]">
          {t('dashboard.startShopping')}
        </Link>
      </section>

      <ul className="mb-6 grid gap-4 sm:grid-cols-3">
        {shortcuts.map((s) => (
          <li key={s.to}>
            <Link to={s.to} className="block h-full rounded-3xl border border-gray-200 bg-gray-50 p-6 transition duration-base hover:-translate-y-1 hover:shadow-token">
              <p className="text-lg font-semibold">{s.title}</p>
              <p className="mt-1 text-gray-500">{s.text}</p>
            </Link>
          </li>
        ))}
      </ul>

      <div className="grid gap-6 empty:hidden md:grid-cols-2">
        <LoyaltyCard />
        <PushCard />
      </div>

      <section className={`mt-6 ${accountPanel}`} aria-labelledby="recent-orders">
        <div className="mb-4 flex items-center justify-between">
          <h2 id="recent-orders" className="text-xl font-semibold">{t('dashboard.recentOrders')}</h2>
          <Link to="/account/orders" className="rounded-full border border-brand px-4 py-1.5 text-sm font-medium text-brand transition-colors hover:bg-brand-light">{t('dashboard.viewAll')}</Link>
        </div>
        {orders === null && <p className="text-gray-500">{t('dashboard.loading')}</p>}
        {orders !== null && recent.length === 0 && (
          <div className="rounded-2xl bg-brand-light px-6 py-10 text-center text-gray-700">
            <p>{t('dashboard.noOrders')}</p>
            <Link to="/shop" className="mt-4 inline-block rounded-full bg-brand px-6 py-2.5 text-sm font-semibold text-white hover:bg-brand-dark">{t('dashboard.startShopping')}</Link>
          </div>
        )}
        <ul className="space-y-3">
          {recent.map((order) => (
            <li key={order.id}>
              <Link to={`/orders/${order.id}`} className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-gray-200 bg-white px-5 py-4 transition duration-base hover:shadow-token">
                <span>
                  <span className="block font-semibold">{order.order_number}</span>
                  <span className="text-sm text-gray-500">{formatDate(order.created_at)}</span>
                </span>
                <span className="flex items-center gap-3">
                  <span className={statusPill}>{t(`orderStatus.statusLabels.${order.status}`)}</span>
                  <span className="font-semibold">{order.currency} {Number(order.total_amount).toFixed(2)}</span>
                </span>
              </Link>
            </li>
          ))}
        </ul>
      </section>
    </div>
  )
}
