import { useEffect, useState } from 'react'
import { Link, Navigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { useLocale } from '../context/LocaleContext'
import { listMyOrders } from '../api/orders'
import AccountNav from '../components/account/AccountNav'

export default function OrdersHistory() {
  const { t } = useLocale()
  const { user, loading: authLoading } = useAuth()
  const [orders, setOrders] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!user) return
    listMyOrders().then(setOrders).finally(() => setLoading(false))
  }, [user])

  if (authLoading) return null
  if (!user) return <Navigate to="/login" replace />

  return (
    <div className="max-w-3xl mx-auto px-4 py-8">
      <AccountNav />
      <h1 className="text-2xl font-bold mb-6">{t('ordersHistory.title')}</h1>
      {loading && <p>{t('ordersHistory.loading')}</p>}
      {!loading && orders.length === 0 && (
        <p className="text-gray-500">{t('ordersHistory.empty')}</p>
      )}
      <ul className="divide-y divide-gray-200">
        {orders.map((order) => (
          <li key={order.id} className="py-3">
            <Link to={`/orders/${order.id}`} className="flex justify-between text-sm">
              <span>
                <span className="font-medium">{order.order_number}</span>
                <span className="text-gray-500"> — {new Date(order.created_at).toLocaleDateString()}</span>
              </span>
              <span>
                {order.status} · {order.currency} {Number(order.total_amount).toFixed(2)}
              </span>
            </Link>
          </li>
        ))}
      </ul>
    </div>
  )
}
