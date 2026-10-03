import { useState } from 'react'
import { apiRequest, errorMessage } from '../../api/client'
import { useLocale } from '../../context/LocaleContext'

// Contents of a set / pack SKU: one "CODE x qty" line per item.
export default function SkuBundle({ sku, onChanged }) {
  const { t } = useLocale()
  const [text, setText] = useState((sku.bundle_items || []).map((i) => `${i.sku_code} x ${i.quantity}`).join('\n'))
  const [error, setError] = useState(null)
  const [saved, setSaved] = useState(false)

  const save = async (e) => {
    e.preventDefault()
    setError(null)
    setSaved(false)
    const items = []
    for (const line of text.split('\n').map((l) => l.trim()).filter(Boolean)) {
      const m = line.match(/^(.+?)\s*[x×*:]\s*(\d+)$/i)
      if (!m) {
        setError(t('admin.productDetail.bundleInvalid'))
        return
      }
      items.push({ sku_code: m[1].trim(), quantity: Number(m[2]) })
    }
    try {
      await apiRequest(`/admin/skus/${sku.id}/bundle`, { method: 'PUT', body: { items } })
      setSaved(true)
      await onChanged()
    } catch (err) {
      setError(errorMessage(err, t('admin.productDetail.skuSaveFailed')))
    }
  }

  return (
    <form onSubmit={save} className="mt-3">
      <textarea rows={3} value={text} onChange={(e) => { setText(e.target.value); setSaved(false) }} placeholder="SKU-350-TR x 3" aria-label={t('admin.productDetail.bundleItems')} className="w-full border border-gray-300 rounded px-2 py-1.5 text-sm font-mono" />
      <p className="text-xs text-gray-500 mb-1">{t('admin.productDetail.bundleItems')}</p>
      <button type="submit" className="border border-gray-300 rounded px-3 py-1.5 text-sm">{t('admin.productDetail.saveBundle')}</button>
      {saved && <span role="status" className="text-xs text-green-700 ml-2">✓</span>}
      {error && <span role="alert" className="text-xs text-red-600 ml-2">{error}</span>}
    </form>
  )
}
