import { useEffect, useState } from 'react'
import { adminCreatePromoCode, adminListPromoCodes, adminUpdatePromoCode } from '../../api/admin'
import { errorMessage } from '../../api/client'
import { useLocale } from '../../context/LocaleContext'
import Money from '../../components/admin/Money'

const emptyForm = { code: '', discount_type: 'percent', discount_value: '', currency: '', min_order_amount: 0, max_uses: '', is_active: true }

export default function AdminPromoCodes() {
  const { t } = useLocale()
  const [codes, setCodes] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [editingId, setEditingId] = useState(null)
  const [form, setForm] = useState(emptyForm)
  const [formOpen, setFormOpen] = useState(false)
  const [formError, setFormError] = useState(null)
  const [submitting, setSubmitting] = useState(false)

  const load = () => adminListPromoCodes().then(setCodes).catch((err) => setError(errorMessage(err, t('admin.promoCodes.loadFailed')))).finally(() => setLoading(false))
  useEffect(() => { load() }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const update = (field) => (e) => {
    const value = e.target.type === 'checkbox' ? e.target.checked : e.target.value
    setForm((f) => ({ ...f, [field]: value }))
  }

  const openNew = () => { setEditingId(null); setForm(emptyForm); setFormError(null); setFormOpen(true) }
  const openEdit = (c) => {
    setEditingId(c.id)
    setForm({ code: c.code, discount_type: c.discount_type, discount_value: c.discount_value, currency: c.currency || '', min_order_amount: c.min_order_amount, max_uses: c.max_uses ?? '', is_active: c.is_active })
    setFormError(null)
    setFormOpen(true)
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setFormError(null)
    setSubmitting(true)
    try {
      const payload = {
        discount_type: form.discount_type,
        discount_value: Number(form.discount_value),
        currency: form.currency || null,
        min_order_amount: Number(form.min_order_amount || 0),
        max_uses: form.max_uses === '' ? null : Number(form.max_uses),
        is_active: form.is_active,
      }
      if (editingId) {
        await adminUpdatePromoCode(editingId, payload)
      } else {
        await adminCreatePromoCode({ ...payload, code: form.code })
      }
      setFormOpen(false)
      await load()
    } catch (err) {
      setFormError(errorMessage(err, t('admin.promoCodes.saveFailed')))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-2xl font-bold">{t('admin.promoCodes.title')}</h1>
        {!formOpen && <button onClick={openNew} className="bg-brand text-white px-4 py-2 rounded text-sm font-medium">{t('admin.promoCodes.add')}</button>}
      </div>

      {loading && <p>{t('admin.common.loading')}</p>}
      {error && <p role="alert" className="text-red-600 text-sm mb-3">{error}</p>}

      {formOpen && (
        <form onSubmit={handleSubmit} className="border border-gray-200 rounded-lg p-4 mb-6 grid grid-cols-2 gap-3">
          <input required disabled={!!editingId} placeholder={t('admin.promoCodes.code')} aria-label={t('admin.promoCodes.code')} value={form.code} onChange={update('code')} className="border border-gray-300 rounded px-3 py-2 text-sm disabled:bg-gray-100" />
          <select value={form.discount_type} aria-label={t('admin.promoCodes.discount')} onChange={update('discount_type')} className="border border-gray-300 rounded px-3 py-2 text-sm">
            <option value="percent">{t('admin.promoCodes.percent')}</option>
            <option value="fixed">{t('admin.promoCodes.fixed')}</option>
          </select>
          <input required type="number" step="0.01" min="0.01" placeholder={t('admin.promoCodes.discountValue')} aria-label={t('admin.promoCodes.discountValue')} value={form.discount_value} onChange={update('discount_value')} className="border border-gray-300 rounded px-3 py-2 text-sm" />
          <input placeholder={t('admin.promoCodes.currencyForFixed')} aria-label={t('admin.promoCodes.currencyForFixed')} maxLength={3} value={form.currency} onChange={update('currency')} className="border border-gray-300 rounded px-3 py-2 text-sm" />
          <input type="number" step="0.01" min="0" placeholder={t('admin.promoCodes.minOrderAmount')} aria-label={t('admin.promoCodes.minOrderAmount')} value={form.min_order_amount} onChange={update('min_order_amount')} className="border border-gray-300 rounded px-3 py-2 text-sm" />
          <input type="number" min="1" placeholder={t('admin.promoCodes.maxUses')} aria-label={t('admin.promoCodes.maxUses')} value={form.max_uses} onChange={update('max_uses')} className="border border-gray-300 rounded px-3 py-2 text-sm" />
          <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={form.is_active} onChange={update('is_active')} /> {t('admin.common.active')}</label>
          {formError && <p role="alert" className="text-sm text-red-600 col-span-2">{formError}</p>}
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
                <th className="px-3 py-2">{t('admin.promoCodes.code')}</th>
                <th className="px-3 py-2">{t('admin.promoCodes.discount')}</th>
                <th className="px-3 py-2">{t('admin.promoCodes.uses')}</th>
                <th className="px-3 py-2">{t('admin.common.active')}</th>
                <th className="px-3 py-2"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {codes.map((c) => (
                <tr key={c.id} className="hover:bg-gray-50">
                  <td className="px-3 py-2 font-medium">{c.code}</td>
                  <td className="px-3 py-2">
                    {c.discount_type === 'percent' ? `${c.discount_value}%` : <Money amount={c.discount_value} currency={c.currency || 'USD'} />}
                  </td>
                  <td className="px-3 py-2">{c.used_count}{c.max_uses ? ` / ${c.max_uses}` : ''}</td>
                  <td className="px-3 py-2">{c.is_active ? t('admin.common.yes') : t('admin.common.no')}</td>
                  <td className="px-3 py-2 text-right"><button onClick={() => openEdit(c)} className="text-brand">{t('admin.common.edit')}</button></td>
                </tr>
              ))}
              {codes.length === 0 && <tr><td colSpan={5} className="px-3 py-6 text-center text-gray-400">{t('admin.promoCodes.none')}</td></tr>}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
