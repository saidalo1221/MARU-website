import { useEffect, useState } from 'react'
import { apiRequest, errorMessage } from '../../api/client'
import { useLocale } from '../../context/LocaleContext'
import { formatDate } from '../../lib/format'

const TYPES = ['invoice', 'proforma_invoice', 'order_confirmation', 'packing_list', 'fiscal_receipt', 'shipping_document', 'return_document', 'other']
const GENERATED = ['order_confirmation', 'proforma_invoice', 'invoice', 'packing_list']

export default function OrderDocumentsPanel({ orderId }) {
  const { t } = useLocale()
  const [docs, setDocs] = useState([])
  const [docType, setDocType] = useState('invoice')
  const [file, setFile] = useState(null)
  const [externalId, setExternalId] = useState('')
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)

  const load = () => apiRequest(`/admin/orders/${orderId}/documents`).then(setDocs).catch(() => setDocs([]))
  useEffect(() => { load() }, [orderId]) // eslint-disable-line react-hooks/exhaustive-deps

  const upload = async (e) => {
    e.preventDefault()
    if (!file) return
    setError(null)
    setBusy(true)
    try {
      const body = new FormData()
      body.append('file', file)
      body.append('doc_type', docType)
      if (externalId) body.append('external_id', externalId)
      await apiRequest(`/admin/orders/${orderId}/documents`, { method: 'POST', body })
      setFile(null)
      setExternalId('')
      e.target.reset()
      await load()
    } catch (err) {
      setError(errorMessage(err, t('admin.orderDetail.documentFailed')))
    } finally {
      setBusy(false)
    }
  }

  const generate = async (docType) => {
    setError(null)
    try {
      await apiRequest(`/admin/orders/${orderId}/documents/generate`, { method: 'POST', body: { doc_type: docType } })
      await load()
    } catch (err) {
      setError(errorMessage(err, t('admin.orderDetail.documentGenerateFailed')))
    }
  }

  const voidDoc = async (id) => {
    await apiRequest(`/admin/orders/${orderId}/documents/${id}/void`, { method: 'POST' })
    await load()
  }

  return (
    <div className="border border-gray-200 rounded-lg p-4">
      <h2 className="font-semibold mb-3">{t('admin.orderDetail.documents')}</h2>
      {docs.length === 0 ? (
        <p className="text-sm text-gray-500 mb-3">{t('admin.orderDetail.documentsNone')}</p>
      ) : (
        <ul className="mb-4 space-y-1 text-sm">
          {docs.map((d) => (
            <li key={d.id} className="flex items-center justify-between gap-3">
              <span className={`min-w-0 truncate ${d.status === 'void' ? 'line-through text-gray-400' : ''}`}>
                {t(`orderStatus.docType_${d.doc_type}`)} · {d.filename} · {formatDate(d.created_at)}
                {d.status === 'void' ? ` (${t('admin.orderDetail.documentVoided')})` : ''}
              </span>
              {d.status !== 'void' && <button type="button" onClick={() => voidDoc(d.id)} className="text-red-600 shrink-0">{t('admin.orderDetail.documentVoid')}</button>}
            </li>
          ))}
        </ul>
      )}
      <div className="mb-4">
        <p className="text-xs text-gray-500 mb-1">{t('admin.orderDetail.documentGenerate')}</p>
        <div className="flex flex-wrap gap-2">
          {GENERATED.map((g) => <button key={g} type="button" onClick={() => generate(g)} className="border border-gray-300 rounded px-2 py-1 text-xs">{t(`orderStatus.docType_${g}`)}</button>)}
        </div>
        <p className="text-xs text-gray-500 mt-1">{t('admin.orderDetail.documentGenerateHint')}</p>
      </div>
      <form onSubmit={upload} className="space-y-2">
        <select value={docType} onChange={(e) => setDocType(e.target.value)} aria-label={t('admin.orderDetail.documentType')} className="w-full border border-gray-300 rounded px-3 py-2 text-sm">
          {TYPES.map((x) => <option key={x} value={x}>{t(`orderStatus.docType_${x}`)}</option>)}
        </select>
        <input type="file" required accept="application/pdf,image/jpeg,image/png" aria-label={t('admin.orderDetail.documentFile')} onChange={(e) => setFile(e.target.files[0] || null)} className="w-full text-sm" />
        <input value={externalId} onChange={(e) => setExternalId(e.target.value)} placeholder={t('admin.orderDetail.documentExternalId')} aria-label={t('admin.orderDetail.documentExternalId')} className="w-full border border-gray-300 rounded px-3 py-2 text-sm" />
        {error && <p role="alert" className="text-sm text-red-600">{error}</p>}
        <button type="submit" disabled={busy || !file} className="bg-brand text-white rounded px-4 py-2 text-sm font-medium disabled:opacity-40">{t('admin.orderDetail.documentUpload')}</button>
      </form>
    </div>
  )
}
