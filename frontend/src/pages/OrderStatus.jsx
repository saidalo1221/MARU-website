import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { cancelOrder, getOrder } from '../api/orders'
import { useLocale } from '../context/LocaleContext'

const CANCELLABLE = new Set(['NEW', 'PAYMENT_PENDING', 'PAID', 'PROCESSING'])

export default function OrderStatus() {
  const { t } = useLocale()
  const { orderId } = useParams()
  const [order, setOrder] = useState(null)
  const [error, setError] = useState(null)
  const [cancelling, setCancelling] = useState(false)

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

  const handleCancel = async () => {
    setCancelling(true)
    try {
      await cancelOrder(orderId, orderToken)
      load()
    } finally {
      setCancelling(false)
    }
  }

  if (error) return <p className="max-w-2xl mx-auto px-4 py-8 text-red-600">{t('orderStatus.notFound')}</p>
  if (!order) return <p className="max-w-2xl mx-auto px-4 py-8">{t('orderStatus.loading')}</p>

  return (
    <div className="max-w-2xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold mb-1">{t('orderStatus.title')}</h1>
      <p className="text-gray-500 mb-6">{t('orderStatus.orderNumber', { number: order.order_number })}</p>

      <div className="border border-gray-200 rounded-lg p-4 mb-6">
        <div className="flex justify-between text-sm mb-2">
          <span className="text-gray-500">{t('orderStatus.status')}</span>
          <span className="font-medium">{order.status}</span>
        </div>
        <div className="flex justify-between text-sm mb-2">
          <span className="text-gray-500">{t('orderStatus.paymentStatus')}</span>
          <span className="font-medium">{order.payment_method || '—'}</span>
        </div>
        <div className="flex justify-between text-sm mb-2">
          <span className="text-gray-500">{t('orderStatus.shippingTo')}</span>
          <span className="font-medium">{order.city}, {order.country}</span>
        </div>
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

      {order.status_history?.length > 0 && (
        <div className="mb-6">
          <h2 className="font-semibold mb-2">{t('orderStatus.history')}</h2>
          <ul className="text-xs text-gray-500 space-y-1">
            {order.status_history.map((h, i) => (
              <li key={i}>{h.to_status} — {new Date(h.created_at).toLocaleString()}</li>
            ))}
          </ul>
        </div>
      )}

      <div className="flex gap-3">
        <Link to="/shop" className="border border-gray-300 rounded px-4 py-2 text-sm">
          {t('cart.continueShopping')}
        </Link>
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
    </div>
  )
}
