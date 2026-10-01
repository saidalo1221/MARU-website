import { useEffect, useState } from 'react'
import { adminGetSkuCost, adminSetSkuCost } from '../../api/admin'
import { errorMessage } from '../../api/client'
import { useLocale } from '../../context/LocaleContext'

// Internal cost per unit (for gross profit on the dashboard); loaded separately so it never travels
// with the public product data.
export default function SkuCost({ sku }) {
  const { t } = useLocale()
  const [value, setValue] = useState('')
  const [error, setError] = useState(null)
  const [saved, setSaved] = useState(false)

  useEffect(() => {
    adminGetSkuCost(sku.id).then((r) => setValue(r.cost_price ?? '')).catch(() => {})
  }, [sku.id])

  const save = async (e) => {
    e.preventDefault()
    setError(null)
    setSaved(false)
    try {
      await adminSetSkuCost(sku.id, value === '' ? null : Number(value))
      setSaved(true)
    } catch (err) {
      setError(errorMessage(err, t('admin.productDetail.skuSaveFailed')))
    }
  }

  return (
    <form onSubmit={save} className="flex flex-wrap items-center gap-2 mt-3">
      <input type="number" min="0" step="0.01" placeholder={t('admin.productDetail.costPrice')} aria-label={t('admin.productDetail.costPrice')} value={value} onChange={(e) => { setValue(e.target.value); setSaved(false) }} className="flex-1 min-w-[12rem] border border-gray-300 rounded px-2 py-1.5 text-sm" />
      <span className="text-xs text-gray-500">{sku.currency}</span>
      <button type="submit" className="border border-gray-300 rounded px-3 py-1.5 text-sm">{t('admin.productDetail.saveCost')}</button>
      {saved && <span role="status" className="text-xs text-green-700">✓</span>}
      {error && <span role="alert" className="text-xs text-red-600">{error}</span>}
    </form>
  )
}
