import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { adminListOrders } from '../../api/admin'
import { errorMessage } from '../../api/client'
import { useLocale } from '../../context/LocaleContext'
import Money from '../../components/admin/Money'

const STATUSES = [
  'new', 'payment_pending', 'paid', 'processing', 'packed', 'shipped', 'in_transit',
  'delivered', 'cancelled', 'returned', 'refunded', 'payment_failed', 'partially_refunded',
]

export default function AdminOrders() {
  const { t } = useLocale()
  const [orders, setOrders] = useState([])
  const [statusFilter, setStatusFilter] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    setLoading(true)
    setError(null)
    adminListOrders(statusFilter || undefined)
      .then(setOrders)
      .catch((err) => setError(errorMessage(err, t('admin.orders.loadFailed'))))
      .finally(() => setLoading(false))
  }, [statusFilter]) // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-2xl font-bold">{t('admin.orders.title')}</h1>
        <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} className="border border-gray-300 rounded px-2 py-1.5 text-sm">
          <option value="">{t('admin.common.allStatuses')}</option>
          {STATUSES.map((s) => <option key={s} value={s}>{s}</option>)}
        </select>
      </div>

      {loading && <p>{t('admin.common.loading')}</p>}
      {error && <p className="text-red-600 text-sm">{error}</p>}

      {!loading && !error && (
        <div className="border border-gray-200 rounded-lg overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-left">
              <tr>
                <th className="px-3 py-2">{t('admin.orders.orderNumber')}</th>
                <th className="px-3 py-2">{t('admin.orders.customer')}</th>
                <th className="px-3 py-2">{t('admin.common.status')}</th>
                <th className="px-3 py-2">{t('admin.orders.total')}</th>
                <th className="px-3 py-2">{t('admin.orders.created')}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {orders.map((o) => (
                <tr key={o.id} className="hover:bg-gray-50">
                  <td className="px-3 py-2">
                    <Link to={`/admin/orders/${o.id}`} className="text-brand font-medium">{o.order_number}</Link>
                  </td>
                  <td className="px-3 py-2">{o.first_name} {o.last_name}</td>
                  <td className="px-3 py-2">{o.status}</td>
                  <td className="px-3 py-2"><Money amount={o.total_amount} currency={o.currency} showOriginal /></td>
                  <td className="px-3 py-2 text-gray-500">{new Date(o.created_at).toLocaleDateString()}</td>
                </tr>
              ))}
              {orders.length === 0 && (
                <tr><td colSpan={5} className="px-3 py-6 text-center text-gray-400">{t('admin.orders.none')}</td></tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
