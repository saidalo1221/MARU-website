import { useState } from 'react'
import { adminReplaceSkuTiers } from '../../api/admin'
import { errorMessage } from '../../api/client'
import { useLocale } from '../../context/LocaleContext'

const inputCls = 'border border-gray-300 rounded px-3 py-2 text-sm'

// Quantity-break prices for one SKU (PRD ТЗ№2 §15), e.g. "from 10 pcs: 8.50".
// Saving replaces the SKU's whole tier list.
export default function SkuTiers({ sku, onChanged }) {
  const { t } = useLocale()
  const [rows, setRows] = useState(() =>
    (sku.quantity_tiers || []).map((tier) => ({ min_quantity: String(tier.min_quantity), price: String(tier.price) }))
  )
  const [error, setError] = useState(null)
  const [saved, setSaved] = useState(false)
  const [busy, setBusy] = useState(false)

  const setRow = (index, field) => (e) => {
    setSaved(false)
    setRows((list) => list.map((row, i) => (i === index ? { ...row, [field]: e.target.value } : row)))
  }

  const save = async (e) => {
    e.preventDefault()
    setError(null)
    setBusy(true)
    try {
      await adminReplaceSkuTiers(
        sku.id,
        rows.map((r) => ({ min_quantity: Number(r.min_quantity), price: Number(r.price) }))
      )
      setSaved(true)
      await onChanged()
    } catch (err) {
      setError(errorMessage(err, t('admin.productDetail.tiersSaveFailed')))
    } finally {
      setBusy(false)
    }
  }

  return (
    <form onSubmit={save} className="mt-3 border-t border-gray-100 pt-3">
      <p className="text-xs font-semibold text-gray-500 uppercase mb-1">{t('admin.productDetail.tiers')}</p>
      <p className="text-xs text-gray-500 mb-2">{t('admin.productDetail.tiersHint', { currency: sku.currency })}</p>
      {rows.map((row, i) => (
        <div key={i} className="flex gap-2 mb-2 items-center">
          <input required type="number" min="2" step="1" placeholder={t('admin.productDetail.tierMinQty')} aria-label={t('admin.productDetail.tierMinQty')} value={row.min_quantity} onChange={setRow(i, 'min_quantity')} className={`${inputCls} w-32`} />
          <input required type="number" min="0.01" step="0.01" placeholder={t('admin.productDetail.tierPrice')} aria-label={t('admin.productDetail.tierPrice')} value={row.price} onChange={setRow(i, 'price')} className={`${inputCls} w-32`} />
          <button type="button" onClick={() => setRows((list) => list.filter((_, j) => j !== i))} className="text-sm text-red-600">
            {t('admin.common.delete')}
          </button>
        </div>
      ))}
      {error && <p role="alert" className="text-red-600 text-xs mb-2">{error}</p>}
      {saved && <p role="status" className="text-green-700 text-xs mb-2">{t('admin.productDetail.tiersSaved')}</p>}
      <div className="flex gap-3">
        <button type="button" onClick={() => setRows((list) => [...list, { min_quantity: '', price: '' }])} className="text-sm text-brand">
          {t('admin.productDetail.addTier')}
        </button>
        <button type="submit" disabled={busy} className="bg-brand text-white rounded px-3 py-1.5 text-sm disabled:opacity-40">
          {t('admin.productDetail.saveTiers')}
        </button>
      </div>
    </form>
  )
}
