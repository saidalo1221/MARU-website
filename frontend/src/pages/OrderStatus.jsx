import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { cancelOrder, getOrder, retryPayment } from '../api/orders'
import { errorMessage } from '../api/client'
import { getShippingEstimate } from '../api/shipping'
import { useAuth } from '../context/AuthContext'
import { useCart } from '../context/CartContext'
import { useLocale } from '../context/LocaleContext'
import { reorder } from '../lib/reorder'
import Seo from '../components/Seo'
import ShipmentList from '../components/ShipmentList'

const CANCELLABLE = new Set(['new', 'payment_pending', 'paid', 'processing'])
const PAID_STATUSES = new Set(['paid', 'processing', 'packed', 'shipped', 'in_transit', 'delivered', 'returned'])
const AWAITING_PAYMENT = new Set(['new', 'payment_pending'])

// What the customer should read as the payment state, derived from the order status.
function paymentState(status) {
  if (PAID_STATUSES.has(status)) return 'Paid'
  if (status === 'payment_failed') return 'Failed'
  if (AWAITING_PAYMENT.has(status)) return 'Pending'
  if (status === 'refunded' || status === 'partially_refunded') return 'Refunded'
  return 'Cancelled'
}

export default function OrderStatus() {
  const { t } = useLocale()
  const { user } = useAuth()
  const { addItem } = useCart()
  const navigate = useNavigate()
  const { orderId } = useParams()
  const [order, setOrder] = useState(null)
  const [error, setError] = useState(null)
  const [cancelling, setCancelling] = useState(false)
  const [estimate, setEstimate] = useState(null)
  const [paying, setPaying] = useState(false)
  const [payError, setPayError] = useState(null)
  const [reordering, setReordering] = useState(false)
  const [reorderNote, setReorderNote] = useState(null)

  const orderToken = sessionStorage.getItem(`maru_order_token_${orderId}`)

  const load = () => {
    getOrder(orderId, orderToken)
      .then(setOrder)
      .catch(setError)
  }

  useEffect(() => {
    load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [orderId])

  useEffect(() => {
    if (!order) return
    getShippingEstimate(order.country).then(setEstimate).catch(() => setEstimate(null))
  }, [order])

  const handleCancel = async () => {
    setCancelling(true)
    try {
      await cancelOrder(orderId, orderToken)
      load()
    } finally {
      setCancelling(false)
    }
  }

  const handlePay = async () => {
    setPayError(null)
    setPaying(true)
    try {
      const payment = await retryPayment(orderId, orderToken)
      window.location.href = payment.reference
    } catch (err) {
      setPayError(errorMessage(err, t('orderStatus.payFailed')))
      setPaying(false)
    }
  }

  const handleReorder = async () => {
    setReorderNote(null)
    setReordering(true)
    try {
      const { added, skipped } = await reorder(order, addItem)
      if (added === 0) {
        setReorderNote(t('orderStatus.reorderFailed'))
      } else if (skipped > 0) {
        setReorderNote(t('orderStatus.reorderPartial'))
        navigate('/cart')
      } else {
        navigate('/cart')
      }
    } finally {
      setReordering(false)
    }
  }

  if (error) return <div role="alert" className="max-w-2xl mx-auto px-4 py-8"><h1 className="text-red-600">{t('orderStatus.notFound')}</h1></div>
  if (!order) return <h1 className="max-w-2xl mx-auto px-4 py-8 font-normal">{t('orderStatus.loading')}</h1>

  const payState = paymentState(order.status)
  const canPay = AWAITING_PAYMENT.has(order.status) || order.status === 'payment_failed'
  const days = estimate && estimate.max_days != null
    ? (estimate.min_days != null && estimate.min_days !== estimate.max_days ? `${estimate.min_days}–${estimate.max_days}` : `${estimate.max_days}`)
    : null
  const row = 'flex justify-between gap-4 text-sm mb-2'

  return (
    <div className="max-w-2xl mx-auto px-4 py-8">
      <Seo title={t('orderStatus.title')} noindex />
      <h1 className="text-2xl font-bold mb-1">{t('orderStatus.title')}</h1>
      <p className="text-gray-500 mb-4">{t('orderStatus.orderNumber', { number: order.order_number })}</p>

      {!user && orderToken && (
        <p className="mb-4 rounded border border-gray-200 px-3 py-2 text-sm">
          {t('orderStatus.createAccount')}{' '}
          <Link to={`/register?email=${encodeURIComponent(order.email)}&next=/account/orders`} className="text-brand underline">{t('orderStatus.createAccountLink')}</Link>
        </p>
      )}
      {payState === 'Paid' && (
        <p role="status" className="mb-4 rounded border border-green-300 bg-green-50 px-3 py-2 text-sm text-green-800">{t('orderStatus.paymentSuccessful')}</p>
      )}
      {payState === 'Failed' && (
        <p role="alert" className="mb-4 rounded border border-red-300 bg-red-50 px-3 py-2 text-sm text-red-800">{t('orderStatus.paymentFailedTitle')}</p>
      )}
      {payState === 'Pending' && (
        <p role="status" className="mb-4 rounded border border-yellow-300 bg-yellow-50 px-3 py-2 text-sm text-yellow-900">{t('orderStatus.paymentWaiting')}</p>
      )}
      {canPay && (
        <div className="mb-4">
          <button onClick={handlePay} disabled={paying} className="bg-brand text-white rounded px-4 py-2 text-sm font-medium disabled:opacity-40">
            {payState === 'Failed' ? t('orderStatus.tryAgain') : t('orderStatus.payNow')}
          </button>
          {payError && <p role="alert" className="mt-2 text-sm text-red-600">{payError}</p>}
        </div>
      )}

      <div className="border border-gray-200 rounded-lg p-4 mb-6">
        <div className={row}>
          <span className="text-gray-500">{t('orderStatus.date')}</span>
          <span className="font-medium">{new Date(order.created_at).toLocaleDateString()}</span>
        </div>
        <div className={row}>
          <span className="text-gray-500">{t('orderStatus.status')}</span>
          <span className="font-medium">{t(`orderStatus.statusLabels.${order.status}`)}</span>
        </div>
        <div className={row}>
          <span className="text-gray-500">{t('orderStatus.paymentMethod')}</span>
          <span className="font-medium">{order.payment_method || '—'}</span>
        </div>
        <div className={row}>
          <span className="text-gray-500">{t('orderStatus.paymentState')}</span>
          <span className="font-medium">{t(`orderStatus.payState${payState}`)}</span>
        </div>
        {order.delivery_method && order.delivery_method !== '*' && (
          <div className={row}>
            <span className="text-gray-500">{t('orderStatus.deliveryMethod')}</span>
            <span className="font-medium">{order.delivery_method}</span>
          </div>
        )}
        <div className={row}>
          <span className="text-gray-500">{t('orderStatus.shippingTo')}</span>
          <span className="font-medium text-right">
            {[order.address_line, order.city, order.region, order.postal_code, order.country].filter(Boolean).join(', ')}
          </span>
        </div>
        {days && (
          <div className={row}>
            <span className="text-gray-500">{t('orderStatus.estimatedDelivery')}</span>
            <span className="font-medium">{t('orderStatus.estimatedDays', { days })}</span>
          </div>
        )}
        <div className="flex justify-between text-sm">
          <span className="text-gray-500">{t('orderStatus.total')}</span>
          <span className="font-medium">{order.currency} {Number(order.total_amount).toFixed(2)}</span>
        </div>
      </div>

      <h2 className="font-semibold mb-2">{t('orderStatus.items')}</h2>
      <ul className="divide-y divide-gray-200 mb-6">
        {order.items.map((item) => (
          <li key={item.id} className="py-2 flex justify-between text-sm">
            <span>{item.product_name_snapshot} × {item.quantity}</span>
            <span>{item.currency} {Number(item.line_total).toFixed(2)}</span>
          </li>
        ))}
      </ul>

      <h2 className="font-semibold mb-2">{t('orderStatus.shipments')}</h2>
      <div className="mb-6">
        <ShipmentList shipments={order.shipments} />
      </div>

      {order.status_history?.length > 0 && (
        <div className="mb-6">
          <h2 className="font-semibold mb-2">{t('orderStatus.history')}</h2>
          <ul className="text-xs text-gray-500 space-y-1">
            {order.status_history.map((h, i) => (
              <li key={i}>{t(`orderStatus.statusLabels.${h.to_status}`)} — {new Date(h.created_at).toLocaleString()}</li>
            ))}
          </ul>
        </div>
      )}

      <div className="flex flex-wrap gap-3">
        <Link to={`/track?order=${encodeURIComponent(order.order_number)}`} className="bg-brand text-white rounded px-4 py-2 text-sm font-medium">
          {t('orderStatus.trackOrder')}
        </Link>
        <Link to="/shop" className="border border-gray-300 rounded px-4 py-2 text-sm">
          {t('cart.continueShopping')}
        </Link>
        {user && order.items.some((i) => i.sku_id) && (
          <button onClick={handleReorder} disabled={reordering} className="border border-gray-300 rounded px-4 py-2 text-sm disabled:opacity-40">
            {reordering ? t('orderStatus.reordering') : t('orderStatus.reorder')}
          </button>
        )}
        {CANCELLABLE.has(order.status) && (
          <button
            onClick={handleCancel}
            disabled={cancelling}
            className="border border-red-400 text-red-600 rounded px-4 py-2 text-sm disabled:opacity-40"
          >
            {cancelling ? t('orderStatus.cancelling') : t('orderStatus.cancelOrder')}
          </button>
        )}
      </div>
      {reorderNote && <p role="alert" className="mt-3 text-sm text-red-600">{reorderNote}</p>}
    </div>
  )
}
