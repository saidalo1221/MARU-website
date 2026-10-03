import { useEffect, useState } from 'react'
import { apiRequest } from '../../api/client'
import { useLocale } from '../../context/LocaleContext'
import { formatDateTime } from '../../lib/format'

// Every payment attempt of the order (ledger rows), so admins see failed tries and provider ids.
export default function PaymentsPanel({ orderId, refreshKey }) {
  const { t } = useLocale()
  const [rows, setRows] = useState([])

  useEffect(() => {
    apiRequest(`/admin/orders/${orderId}/payments`).then(setRows).catch(() => setRows([]))
  }, [orderId, refreshKey])

  return (
    <div className="border border-gray-200 rounded-lg p-4">
      <h2 className="font-semibold mb-3">{t('admin.orderDetail.payments')}</h2>
      {rows.length === 0 ? (
        <p className="text-sm text-gray-500">{t('admin.orderDetail.paymentsNone')}</p>
      ) : (
        <ol className="space-y-2 text-sm">
          {rows.map((p, i) => (
            <li key={p.id} className="flex flex-wrap justify-between gap-x-3">
              <span>
                <span className="font-medium">{t('admin.orderDetail.paymentAttempt', { n: i + 1 })}</span> · {p.provider} · {p.currency} {Number(p.amount).toFixed(2)}
                {p.provider_transaction_id ? ` · ${p.provider_transaction_id}` : ''}
              </span>
              <span className="text-gray-600">
                {t(`orderStatus.payStatus_${p.status}`)}{p.paid_at ? ` · ${formatDateTime(p.paid_at)}` : ''}
              </span>
            </li>
          ))}
        </ol>
      )}
    </div>
  )
}
