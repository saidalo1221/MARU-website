import { useEffect, useState } from 'react'
import { apiRequest, errorMessage } from '../api/client'
import { useLocale } from '../context/LocaleContext'
import { formatDate } from '../lib/format'

// Invoices, receipts and other documents of an order. The file is opened through a short-lived
// signed link, so nothing here is publicly reachable.
export default function OrderDocuments({ orderId, orderToken }) {
  const { t } = useLocale()
  const [docs, setDocs] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    apiRequest(`/orders/${orderId}/documents`, { orderToken })
      .then(setDocs)
      .catch(() => setDocs([]))
  }, [orderId, orderToken])

  const open = async (doc) => {
    setError(null)
    try {
      const { url } = await apiRequest(`/orders/${orderId}/documents/${doc.id}/link`, { method: 'POST', orderToken })
      window.open(url, '_blank', 'noopener')
    } catch (err) {
      setError(errorMessage(err, t('orderStatus.downloadFailed')))
    }
  }

  if (docs === null) return null
  return (
    <section className="mb-6" aria-label={t('orderStatus.documents')}>
      <h2 className="mb-3 text-xl font-semibold">{t('orderStatus.documents')}</h2>
      {docs.length === 0 ? (
        <p className="text-sm text-gray-500">{t('orderStatus.documentsNone')}</p>
      ) : (
        <ul className="space-y-2 text-sm">
          {docs.map((d) => (
            <li key={d.id} className="flex items-center justify-between gap-3 rounded-2xl border border-gray-200 bg-gray-50 px-4 py-3">
              <span className="min-w-0 truncate">
                <span className="font-medium">{t(`orderStatus.docType_${d.doc_type}`)}</span>
                <span className="text-gray-500"> · {d.filename} · {formatDate(d.created_at)}</span>
              </span>
              <button type="button" onClick={() => open(d)} className="text-brand shrink-0">{t('orderStatus.download')}</button>
            </li>
          ))}
        </ul>
      )}
      {error && <p role="alert" className="text-sm text-red-600 mt-2">{error}</p>}
    </section>
  )
}
