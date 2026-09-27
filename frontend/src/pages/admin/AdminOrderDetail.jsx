import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { adminGetOrder, adminRefundOrder, adminUpdateOrderStatus } from '../../api/admin'
import { errorMessage } from '../../api/client'

const STATUSES = [
  'new', 'payment_pending', 'paid', 'processing', 'packed', 'shipped', 'in_transit',
  'delivered', 'cancelled', 'returned', 'refunded', 'payment_failed', 'partially_refunded',
]

export default function AdminOrderDetail() {
  const { orderId } = useParams()
  const [order, setOrder] = useState(null)
  const [error, setError] = useState(null)
  const [statusChoice, setStatusChoice] = useState('')
  const [note, setNote] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [refundAmount, setRefundAmount] = useState('')
  const [refundReason, setRefundReason] = useState('')
  const [refundError, setRefundError] = useState(null)
  const [refundSubmitting, setRefundSubmitting] = useState(false)

  const load = () => adminGetOrder(orderId).then((o) => { setOrder(o); setStatusChoice(o.status) }).catch((err) => setError(errorMessage(err, 'Failed to load order')))

  useEffect(() => { load() }, [orderId]) // eslint-disable-line react-hooks/exhaustive-deps

  if (error) return <p className="text-red-600 text-sm">{error}</p>
  if (!order) return <p>Loading...</p>

  const handleStatusUpdate = async (e) => {
    e.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      await adminUpdateOrderStatus(order.id, statusChoice, note)
      setNote('')
      await load()
    } catch (err) {
      setError(errorMessage(err, 'Failed to update status'))
    } finally {
      setSubmitting(false)
    }
  }

  const handleRefund = async (e) => {
    e.preventDefault()
    setRefundError(null)
    setRefundSubmitting(true)
    try {
      await adminRefundOrder(order.id, Number(refundAmount), refundReason)
      setRefundAmount('')
      setRefundReason('')
      await load()
    } catch (err) {
      setRefundError(errorMessage(err, 'Failed to process refund'))
    } finally {
      setRefundSubmitting(false)
    }
  }

  return (
    <div>
      <Link to="/admin/orders" className="text-sm text-brand">&larr; Back to orders</Link>
      <h1 className="text-2xl font-bold mt-2 mb-1">{order.order_number}</h1>
      <p className="text-sm text-gray-500 mb-6">{order.first_name} {order.last_name} · {order.email}</p>

      <div className="grid md:grid-cols-2 gap-8">
        <div>
          <h2 className="font-semibold mb-2">Items</h2>
          <ul className="divide-y divide-gray-200 mb-4 text-sm">
            {order.items.map((i) => (
              <li key={i.id} className="py-2 flex justify-between">
                <span>{i.product_name_snapshot} ({i.sku_code_snapshot}) × {i.quantity}</span>
                <span>{i.currency} {Number(i.line_total).toFixed(2)}</span>
              </li>
            ))}
          </ul>
          <dl className="text-sm space-y-1 border-t border-gray-200 pt-2">
            <div className="flex justify-between"><dt className="text-gray-500">Subtotal</dt><dd>{order.currency} {Number(order.subtotal_amount).toFixed(2)}</dd></div>
            <div className="flex justify-between"><dt className="text-gray-500">Discount</dt><dd>-{order.currency} {Number(order.discount_amount).toFixed(2)}</dd></div>
            <div className="flex justify-between"><dt className="text-gray-500">Tax</dt><dd>{order.currency} {Number(order.tax_amount).toFixed(2)}</dd></div>
            <div className="flex justify-between"><dt className="text-gray-500">Delivery</dt><dd>{order.currency} {Number(order.delivery_amount).toFixed(2)}</dd></div>
            <div className="flex justify-between font-semibold border-t border-gray-200 pt-1 mt-1"><dt>Total</dt><dd>{order.currency} {Number(order.total_amount).toFixed(2)}</dd></div>
          </dl>

          <h2 className="font-semibold mt-6 mb-2">History</h2>
          <ul className="text-xs text-gray-500 space-y-1">
            {order.status_history.map((h, i) => (
              <li key={i}>{h.from_status ?? '—'} → {h.to_status} · {new Date(h.created_at).toLocaleString()}{h.note ? ` · ${h.note}` : ''}</li>
            ))}
          </ul>
        </div>

        <div className="space-y-6">
          <form onSubmit={handleStatusUpdate} className="border border-gray-200 rounded-lg p-4">
            <h2 className="font-semibold mb-3">Update status</h2>
            <p className="text-sm text-gray-500 mb-2">Current: <span className="font-medium text-gray-900">{order.status}</span></p>
            <select value={statusChoice} onChange={(e) => setStatusChoice(e.target.value)} className="w-full border border-gray-300 rounded px-3 py-2 text-sm mb-2">
              {STATUSES.map((s) => <option key={s} value={s}>{s}</option>)}
            </select>
            <input value={note} onChange={(e) => setNote(e.target.value)} placeholder="Note (optional)" className="w-full border border-gray-300 rounded px-3 py-2 text-sm mb-2" />
            {error && <p className="text-sm text-red-600 mb-2">{error}</p>}
            <button type="submit" disabled={submitting} className="bg-brand text-white rounded px-4 py-2 text-sm font-medium disabled:opacity-40">
              {submitting ? 'Updating...' : 'Update Status'}
            </button>
          </form>

          <form onSubmit={handleRefund} className="border border-gray-200 rounded-lg p-4">
            <h2 className="font-semibold mb-3">Refund</h2>
            <input required type="number" step="0.01" min="0.01" value={refundAmount} onChange={(e) => setRefundAmount(e.target.value)} placeholder={`Amount (${order.currency})`} className="w-full border border-gray-300 rounded px-3 py-2 text-sm mb-2" />
            <input value={refundReason} onChange={(e) => setRefundReason(e.target.value)} placeholder="Reason (optional)" className="w-full border border-gray-300 rounded px-3 py-2 text-sm mb-2" />
            {refundError && <p className="text-sm text-red-600 mb-2">{refundError}</p>}
            <button type="submit" disabled={refundSubmitting} className="border border-red-400 text-red-600 rounded px-4 py-2 text-sm font-medium disabled:opacity-40">
              {refundSubmitting ? 'Processing...' : 'Process Refund'}
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}
