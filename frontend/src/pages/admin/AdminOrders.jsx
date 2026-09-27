import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { adminListOrders } from '../../api/admin'
import { errorMessage } from '../../api/client'

const STATUSES = [
  'new', 'payment_pending', 'paid', 'processing', 'packed', 'shipped', 'in_transit',
  'delivered', 'cancelled', 'returned', 'refunded', 'payment_failed', 'partially_refunded',
]

export default function AdminOrders() {
  const [orders, setOrders] = useState([])
  const [statusFilter, setStatusFilter] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    setLoading(true)
    setError(null)
    adminListOrders(statusFilter || undefined)
      .then(setOrders)
      .catch((err) => setError(errorMessage(err, 'Failed to load orders')))
      .finally(() => setLoading(false))
  }, [statusFilter])

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-2xl font-bold">Orders</h1>
        <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} className="border border-gray-300 rounded px-2 py-1.5 text-sm">
          <option value="">All statuses</option>
          {STATUSES.map((s) => <option key={s} value={s}>{s}</option>)}
        </select>
      </div>

      {loading && <p>Loading...</p>}
      {error && <p className="text-red-600 text-sm">{error}</p>}

      {!loading && !error && (
        <div className="border border-gray-200 rounded-lg overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-left">
              <tr>
                <th className="px-3 py-2">Order #</th>
                <th className="px-3 py-2">Customer</th>
                <th className="px-3 py-2">Status</th>
                <th className="px-3 py-2">Total</th>
                <th className="px-3 py-2">Created</th>
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
                  <td className="px-3 py-2">{o.currency} {Number(o.total_amount).toFixed(2)}</td>
                  <td className="px-3 py-2 text-gray-500">{new Date(o.created_at).toLocaleDateString()}</td>
                </tr>
              ))}
              {orders.length === 0 && (
                <tr><td colSpan={5} className="px-3 py-6 text-center text-gray-400">No orders found.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
