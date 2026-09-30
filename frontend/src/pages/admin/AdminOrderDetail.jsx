import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { adminGetOrder, adminRefundOrder, adminUpdateOrderStatus } from '../../api/admin'
import { errorMessage } from '../../api/client'
import { useLocale } from '../../context/LocaleContext'
import Money from '../../components/admin/Money'

const STATUSES = [
  'new', 'payment_pending', 'paid', 'processing', 'packed', 'shipped', 'in_transit',
  'delivered', 'cancelled', 'returned', 'refunded', 'payment_failed', 'partially_refunded',
]

export default function AdminOrderDetail() {
  const { t } = useLocale()
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

  const load = () => adminGetOrder(orderId).then((o) => { setOrder(o); setStatusChoice(o.status) }).catch((err) => setError(errorMessage(err, t('admin.orderDetail.loadFailed'))))

  useEffect(() => { load() }, [orderId]) // eslint-disable-line react-hooks/exhaustive-deps

  if (error) return <p role="alert" className="text-red-600 text-sm">{error}</p>
  if (!order) return <p>{t('admin.common.loading')}</p>

  const handleStatusUpdate = async (e) => {
    e.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      await adminUpdateOrderStatus(order.id, statusChoice, note)
      setNote('')
      await load()
    } catch (err) {
      setError(errorMessage(err, t('admin.orderDetail.statusFailed')))
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
      setRefundError(errorMessage(err, t('admin.orderDetail.refundFailed')))
    } finally {
      setRefundSubmitting(false)
    }
  }

  return (
    <div>
      <Link to="/admin/orders" className="text-sm text-brand">&larr; {t('admin.orderDetail.back')}</Link>
      <h1 className="text-2xl font-bold mt-2 mb-1">{order.order_number}</h1>
      <p className="text-sm text-gray-500 mb-6">{order.first_name} {order.last_name} · {order.email}</p>

      <div className="grid md:grid-cols-2 gap-8">
        <div>
          <h2 className="font-semibold mb-2">{t('admin.orderDetail.items')}</h2>
          <ul className="divide-y divide-gray-200 mb-4 text-sm">
            {order.items.map((i) => (
              <li key={i.id} className="py-2 flex justify-between">
                <span>{i.product_name_snapshot} ({i.sku_code_snapshot}) × {i.quantity}</span>
                <Money amount={i.line_total} currency={i.currency} showOriginal />
              </li>
            ))}
          </ul>
          <dl className="text-sm space-y-1 border-t border-gray-200 pt-2">
            <div className="flex justify-between"><dt className="text-gray-500">{t('admin.orderDetail.subtotal')}</dt><dd><Money amount={order.subtotal_amount} currency={order.currency} showOriginal /></dd></div>
            <div className="flex justify-between"><dt className="text-gray-500">{t('admin.orderDetail.discount')}</dt><dd>-<Money amount={order.discount_amount} currency={order.currency} showOriginal /></dd></div>
            <div className="flex justify-between"><dt className="text-gray-500">{t('admin.orderDetail.tax')}</dt><dd><Money amount={order.tax_amount} currency={order.currency} showOriginal /></dd></div>
            <div className="flex justify-between"><dt className="text-gray-500">{t('admin.orderDetail.delivery')}</dt><dd><Money amount={order.delivery_amount} currency={order.currency} showOriginal /></dd></div>
            <div className="flex justify-between font-semibold border-t border-gray-200 pt-1 mt-1"><dt>{t('admin.orderDetail.total')}</dt><dd><Money amount={order.total_amount} currency={order.currency} showOriginal /></dd></div>
          </dl>

          <h2 className="font-semibold mt-6 mb-2">{t('admin.orderDetail.history')}</h2>
          <ul className="text-xs text-gray-500 space-y-1">
            {order.status_history.map((h, i) => (
              <li key={i}>{h.from_status ?? '—'} → {h.to_status} · {new Date(h.created_at).toLocaleString()}{h.note ? ` · ${h.note}` : ''}</li>
            ))}
          </ul>
        </div>

        <div className="space-y-6">
          <form onSubmit={handleStatusUpdate} className="border border-gray-200 rounded-lg p-4">
            <h2 className="font-semibold mb-3">{t('admin.orderDetail.updateStatus')}</h2>
            <p className="text-sm text-gray-500 mb-2">{t('admin.orderDetail.current', { status: order.status })}</p>
            <select value={statusChoice} aria-label={t('admin.orderDetail.updateStatus')} onChange={(e) => setStatusChoice(e.target.value)} className="w-full border border-gray-300 rounded px-3 py-2 text-sm mb-2">
              {STATUSES.map((s) => <option key={s} value={s}>{s}</option>)}
            </select>
            <input value={note} onChange={(e) => setNote(e.target.value)} placeholder={t('admin.orderDetail.note')} aria-label={t('admin.orderDetail.note')} className="w-full border border-gray-300 rounded px-3 py-2 text-sm mb-2" />
            {error && <p role="alert" className="text-sm text-red-600 mb-2">{error}</p>}
            <button type="submit" disabled={submitting} className="bg-brand text-white rounded px-4 py-2 text-sm font-medium disabled:opacity-40">
              {submitting ? t('admin.orderDetail.updating') : t('admin.orderDetail.updateButton')}
            </button>
          </form>

          <form onSubmit={handleRefund} className="border border-gray-200 rounded-lg p-4">
            <h2 className="font-semibold mb-3">{t('admin.orderDetail.refund')}</h2>
            <input required type="number" step="0.01" min="0.01" value={refundAmount} onChange={(e) => setRefundAmount(e.target.value)} placeholder={t('admin.orderDetail.amount', { currency: order.currency })} aria-label={t('admin.orderDetail.amount', { currency: order.currency })} className="w-full border border-gray-300 rounded px-3 py-2 text-sm mb-2" />
            <input value={refundReason} onChange={(e) => setRefundReason(e.target.value)} placeholder={t('admin.orderDetail.reason')} aria-label={t('admin.orderDetail.reason')} className="w-full border border-gray-300 rounded px-3 py-2 text-sm mb-2" />
            {refundError && <p role="alert" className="text-sm text-red-600 mb-2">{refundError}</p>}
            <button type="submit" disabled={refundSubmitting} className="border border-red-400 text-red-600 rounded px-4 py-2 text-sm font-medium disabled:opacity-40">
              {refundSubmitting ? t('admin.orderDetail.processing') : t('admin.orderDetail.refundButton')}
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}
