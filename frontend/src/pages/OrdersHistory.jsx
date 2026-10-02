import { useEffect, useState } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { useLocale } from '../context/LocaleContext'
import { listMyOrders } from '../api/orders'
import { useCart } from '../context/CartContext'
import { reorder } from '../lib/reorder'
import AccountNav from '../components/account/AccountNav'
import Seo from '../components/Seo'
import Pagination from '../components/ui/Pagination'
import { PAGE_SIZE } from '../api/client'
import { formatDate } from '../lib/format'

export default function OrdersHistory() {
  const { t } = useLocale()
  const { user, loading: authLoading } = useAuth()
  const [orders, setOrders] = useState([])
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const { addItem } = useCart()
  const navigate = useNavigate()
  const [reorderingId, setReorderingId] = useState(null)
  const [reorderError, setReorderError] = useState(null)

  useEffect(() => {
    if (!user) return
    setLoading(true)
    listMyOrders(page)
      .then(({ data, total: n }) => {
        setOrders(data)
        setTotal(n)
      })
      .finally(() => setLoading(false))
  }, [user, page])

  const handleReorder = async (order) => {
    setReorderError(null)
    setReorderingId(order.id)
    try {
      const { added } = await reorder(order, addItem)
      if (added === 0) setReorderError(t('orderStatus.reorderFailed'))
      else navigate('/cart')
    } finally {
      setReorderingId(null)
    }
  }

  if (authLoading) return null
  if (!user) return <Navigate to="/login" replace />

  return (
    <div className="max-w-3xl mx-auto px-4 py-8">
      <Seo title={t('ordersHistory.title')} noindex />
      <AccountNav />
      <h1 className="mb-6 text-3xl font-semibold tracking-tight md:text-4xl">{t('ordersHistory.title')}</h1>
      {loading && <p>{t('ordersHistory.loading')}</p>}
      {!loading && orders.length === 0 && (
        <div className="rounded-3xl bg-brand-light px-6 py-14 text-center text-gray-700">
          <p>{t('ordersHistory.empty')}</p>
          <Link to="/shop" className="mt-4 inline-block rounded-full bg-brand px-6 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-brand-dark disabled:opacity-40">{t('dashboard.startShopping')}</Link>
        </div>
      )}
      {reorderError && <p role="alert" className="text-sm text-red-600 mb-3">{reorderError}</p>}
      <ul className="space-y-3">
        {orders.map((order) => (
          <li key={order.id} className="flex items-center gap-3 rounded-2xl border border-gray-200 bg-gray-50 px-5 py-4">
            <Link to={`/orders/${order.id}`} className="flex flex-1 justify-between text-sm">
              <span>
                <span className="font-medium">{order.order_number}</span>
                <span className="text-gray-500"> - {formatDate(order.created_at)}</span>
              </span>
              <span>
                {t(`orderStatus.statusLabels.${order.status}`)} · {order.currency} {Number(order.total_amount).toFixed(2)}
              </span>
            </Link>
            {order.items.some((i) => i.sku_id) && (
              <button
                type="button"
                onClick={() => handleReorder(order)}
                disabled={reorderingId === order.id}
                className="rounded-full border border-gray-300 px-4 py-1.5 text-xs font-medium transition-colors hover:bg-brand-light disabled:opacity-40"
              >
                {reorderingId === order.id ? t('orderStatus.reordering') : t('orderStatus.reorder')}
              </button>
            )}
          </li>
        ))}
      </ul>
      <Pagination page={page} pageCount={Math.max(1, Math.ceil(total / PAGE_SIZE))} onChange={setPage} />
    </div>
  )
}
