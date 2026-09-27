import { useEffect, useState } from 'react'
import { adminCreateShippingRate, adminListShippingRates, adminUpdateShippingRate } from '../../api/admin'
import { errorMessage } from '../../api/client'
import { useLocale } from '../../context/LocaleContext'
import Money from '../../components/admin/Money'

const emptyForm = { country: '', delivery_method: '', currency: 'USD', base_fee: 0, per_kg_fee: 0, is_active: true }

// Pass '*' for country or delivery_method to mean "any" — matches the
// backend's wildcard lookup (app/models/shipping_rate.py's ANY sentinel).
export default function AdminShippingRates() {
  const { t } = useLocale()
  const [rates, setRates] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [editingId, setEditingId] = useState(null)
  const [form, setForm] = useState(emptyForm)
  const [formOpen, setFormOpen] = useState(false)
  const [formError, setFormError] = useState(null)
  const [submitting, setSubmitting] = useState(false)

  const load = () => adminListShippingRates().then(setRates).catch((err) => setError(errorMessage(err, t('admin.shippingRates.loadFailed')))).finally(() => setLoading(false))
  useEffect(() => { load() }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const update = (field) => (e) => {
    const value = e.target.type === 'checkbox' ? e.target.checked : e.target.value
    setForm((f) => ({ ...f, [field]: value }))
  }

  const openNew = () => { setEditingId(null); setForm(emptyForm); setFormError(null); setFormOpen(true) }
  const openEdit = (r) => {
    setEditingId(r.id)
    setForm({ country: r.country, delivery_method: r.delivery_method, currency: r.currency, base_fee: r.base_fee, per_kg_fee: r.per_kg_fee, is_active: r.is_active })
    setFormError(null)
    setFormOpen(true)
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setFormError(null)
    setSubmitting(true)
    try {
      const payload = { currency: form.currency, base_fee: Number(form.base_fee), per_kg_fee: Number(form.per_kg_fee), is_active: form.is_active }
      if (editingId) {
        await adminUpdateShippingRate(editingId, payload)
      } else {
        await adminCreateShippingRate({ ...payload, country: form.country, delivery_method: form.delivery_method })
      }
      setFormOpen(false)
      await load()
    } catch (err) {
      setFormError(errorMessage(err, t('admin.shippingRates.saveFailed')))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-2xl font-bold">{t('admin.shippingRates.title')}</h1>
        {!formOpen && <button onClick={openNew} className="bg-brand text-white px-4 py-2 rounded text-sm font-medium">{t('admin.shippingRates.add')}</button>}
      </div>

      {loading && <p>{t('admin.common.loading')}</p>}
      {error && <p className="text-red-600 text-sm mb-3">{error}</p>}

      {formOpen && (
        <form onSubmit={handleSubmit} className="border border-gray-200 rounded-lg p-4 mb-6 grid grid-cols-2 gap-3">
          <input required disabled={!!editingId} placeholder={t('admin.shippingRates.countryWildcard')} value={form.country} onChange={update('country')} className="border border-gray-300 rounded px-3 py-2 text-sm disabled:bg-gray-100" />
          <input required disabled={!!editingId} placeholder={t('admin.shippingRates.methodWildcard')} value={form.delivery_method} onChange={update('delivery_method')} className="border border-gray-300 rounded px-3 py-2 text-sm disabled:bg-gray-100" />
          <input placeholder={t('admin.shippingRates.currency')} maxLength={3} value={form.currency} onChange={update('currency')} className="border border-gray-300 rounded px-3 py-2 text-sm" />
          <input type="number" step="0.01" min="0" placeholder={t('admin.shippingRates.baseFee')} value={form.base_fee} onChange={update('base_fee')} className="border border-gray-300 rounded px-3 py-2 text-sm" />
          <input type="number" step="0.01" min="0" placeholder={t('admin.shippingRates.perKgFee')} value={form.per_kg_fee} onChange={update('per_kg_fee')} className="border border-gray-300 rounded px-3 py-2 text-sm" />
          <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={form.is_active} onChange={update('is_active')} /> {t('admin.common.active')}</label>
          {formError && <p className="text-sm text-red-600 col-span-2">{formError}</p>}
          <div className="col-span-2 flex gap-2">
            <button type="submit" disabled={submitting} className="bg-brand text-white px-4 py-2 rounded text-sm font-medium disabled:opacity-40">{submitting ? t('admin.common.saving') : t('admin.common.save')}</button>
            <button type="button" onClick={() => setFormOpen(false)} className="border border-gray-300 rounded px-4 py-2 text-sm">{t('admin.common.cancel')}</button>
          </div>
        </form>
      )}

      {!loading && (
        <div className="border border-gray-200 rounded-lg overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-left">
              <tr>
                <th className="px-3 py-2">{t('admin.common.country')}</th>
                <th className="px-3 py-2">{t('admin.shippingRates.method')}</th>
                <th className="px-3 py-2">{t('admin.shippingRates.baseFee')}</th>
                <th className="px-3 py-2">{t('admin.shippingRates.perKgFee')}</th>
                <th className="px-3 py-2">{t('admin.common.active')}</th>
                <th className="px-3 py-2"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {rates.map((r) => (
                <tr key={r.id} className="hover:bg-gray-50">
                  <td className="px-3 py-2">{r.country}</td>
                  <td className="px-3 py-2">{r.delivery_method}</td>
                  <td className="px-3 py-2"><Money amount={r.base_fee} currency={r.currency} /></td>
                  <td className="px-3 py-2"><Money amount={r.per_kg_fee} currency={r.currency} /></td>
                  <td className="px-3 py-2">{r.is_active ? t('admin.common.yes') : t('admin.common.no')}</td>
                  <td className="px-3 py-2 text-right"><button onClick={() => openEdit(r)} className="text-brand">{t('admin.common.edit')}</button></td>
                </tr>
              ))}
              {rates.length === 0 && <tr><td colSpan={6} className="px-3 py-6 text-center text-gray-400">{t('admin.shippingRates.none')}</td></tr>}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
