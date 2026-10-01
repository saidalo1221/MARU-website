import { useEffect, useState } from 'react'
import { adminCreateTaxRule, adminListTaxRules, adminUpdateTaxRule } from '../../api/admin'
import { errorMessage } from '../../api/client'
import { useLocale } from '../../context/LocaleContext'

const emptyForm = { country: '', region: '*', customer_type: '', tax_type: 'vat', tax_class: '*', min_order_amount: 0, rate: 0, is_active: true }

// Pass '*' for country or customer_type to mean "any" (same wildcard
// convention as shipping rates).
export default function AdminTaxRules() {
  const { t } = useLocale()
  const [rules, setRules] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [editingId, setEditingId] = useState(null)
  const [form, setForm] = useState(emptyForm)
  const [formOpen, setFormOpen] = useState(false)
  const [formError, setFormError] = useState(null)
  const [submitting, setSubmitting] = useState(false)

  const load = () => adminListTaxRules().then(setRules).catch((err) => setError(errorMessage(err, t('admin.taxRules.loadFailed')))).finally(() => setLoading(false))
  useEffect(() => { load() }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const update = (field) => (e) => {
    const value = e.target.type === 'checkbox' ? e.target.checked : e.target.value
    setForm((f) => ({ ...f, [field]: value }))
  }

  const openNew = () => { setEditingId(null); setForm(emptyForm); setFormError(null); setFormOpen(true) }
  const openEdit = (r) => {
    setEditingId(r.id)
    setForm({ country: r.country, region: r.region, customer_type: r.customer_type, tax_type: r.tax_type, tax_class: r.tax_class || '*', min_order_amount: r.min_order_amount, rate: r.rate, is_active: r.is_active })
    setFormError(null)
    setFormOpen(true)
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setFormError(null)
    setSubmitting(true)
    try {
      const payload = { rate: Number(form.rate), is_active: form.is_active }
      if (editingId) {
        await adminUpdateTaxRule(editingId, payload)
      } else {
        await adminCreateTaxRule({ ...payload, country: form.country, region: form.region || '*', customer_type: form.customer_type, tax_type: form.tax_type, tax_class: form.tax_class, min_order_amount: Number(form.min_order_amount) })
      }
      setFormOpen(false)
      await load()
    } catch (err) {
      setFormError(errorMessage(err, t('admin.taxRules.saveFailed')))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-2xl font-bold">{t('admin.taxRules.title')}</h1>
        {!formOpen && <button onClick={openNew} className="bg-brand text-white px-4 py-2 rounded text-sm font-medium">{t('admin.taxRules.add')}</button>}
      </div>

      {loading && <p>{t('admin.common.loading')}</p>}
      {error && <p role="alert" className="text-red-600 text-sm mb-3">{error}</p>}

      {formOpen && (
        <form onSubmit={handleSubmit} className="border border-gray-200 rounded-lg p-4 mb-6 grid grid-cols-2 gap-3">
          <label className="text-xs text-gray-500 flex flex-col gap-1">{t('admin.taxRules.countryWildcard')}
            <input required disabled={!!editingId} value={form.country} onChange={update('country')} className="border border-gray-300 rounded px-3 py-2 text-sm text-gray-900 disabled:bg-gray-100" />
          </label>
          <label className="text-xs text-gray-500 flex flex-col gap-1">{t('admin.taxRules.regionWildcard')}
            <input required disabled={!!editingId} value={form.region} onChange={update('region')} className="border border-gray-300 rounded px-3 py-2 text-sm text-gray-900 disabled:bg-gray-100" />
          </label>
          <label className="text-xs text-gray-500 flex flex-col gap-1">{t('admin.taxRules.customerTypeWildcard')}
            <input required disabled={!!editingId} value={form.customer_type} onChange={update('customer_type')} className="border border-gray-300 rounded px-3 py-2 text-sm text-gray-900 disabled:bg-gray-100" />
          </label>
          <label className="text-xs text-gray-500 flex flex-col gap-1">{t('admin.taxRules.taxType')}
            <input disabled={!!editingId} value={form.tax_type} onChange={update('tax_type')} className="border border-gray-300 rounded px-3 py-2 text-sm text-gray-900 disabled:bg-gray-100" />
          </label>
          <label className="text-xs text-gray-500 flex flex-col gap-1">{t('admin.taxRules.taxClass')}
            <select disabled={!!editingId} value={form.tax_class} onChange={update('tax_class')} className="border border-gray-300 rounded px-3 py-2 text-sm text-gray-900 disabled:bg-gray-100">
              <option value="*">{t('admin.taxRules.taxClassAny')}</option>
              <option value="reduced">{t('admin.taxRules.taxClassReduced')}</option>
            </select>
          </label>
          <label className="text-xs text-gray-500 flex flex-col gap-1">{t('admin.taxRules.minOrder')}
            <input required type="number" step="0.01" min="0" disabled={!!editingId} value={form.min_order_amount} onChange={update('min_order_amount')} className="border border-gray-300 rounded px-3 py-2 text-sm text-gray-900 disabled:bg-gray-100" />
          </label>
          <label className="text-xs text-gray-500 flex flex-col gap-1">{t('admin.taxRules.rate')}
            <input required type="number" step="0.01" min="0" max="100" value={form.rate} onChange={update('rate')} className="border border-gray-300 rounded px-3 py-2 text-sm text-gray-900" />
          </label>
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
                <th scope="col" className="px-3 py-2">{t('admin.common.country')}</th>
                <th scope="col" className="px-3 py-2">{t('admin.taxRules.region')}</th>
                <th scope="col" className="px-3 py-2">{t('admin.taxRules.customerType')}</th>
                <th scope="col" className="px-3 py-2">{t('admin.taxRules.taxType')}</th>
                <th scope="col" className="px-3 py-2">{t('admin.taxRules.taxClass')}</th>
                <th scope="col" className="px-3 py-2">{t('admin.taxRules.minOrder')}</th>
                <th scope="col" className="px-3 py-2">{t('admin.taxRules.rate')}</th>
                <th scope="col" className="px-3 py-2">{t('admin.common.active')}</th>
                <th scope="col" className="px-3 py-2"><span className="sr-only">{t('admin.common.actions')}</span></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {rules.map((r) => (
                <tr key={r.id} className="hover:bg-gray-50">
                  <td className="px-3 py-2">{r.country}</td>
                  <td className="px-3 py-2">{r.region}</td>
                  <td className="px-3 py-2">{r.customer_type}</td>
                  <td className="px-3 py-2">{r.tax_type}</td>
                  <td className="px-3 py-2">{r.tax_class === 'reduced' ? t('admin.taxRules.taxClassReduced') : t('admin.taxRules.taxClassAny')}</td>
                  <td className="px-3 py-2">{Number(r.min_order_amount)}</td>
                  <td className="px-3 py-2">{Number(r.rate)}%</td>
                  <td className="px-3 py-2">{r.is_active ? t('admin.common.yes') : t('admin.common.no')}</td>
                  <td className="px-3 py-2 text-right"><button onClick={() => openEdit(r)} className="text-brand">{t('admin.common.edit')}</button></td>
                </tr>
              ))}
              {rules.length === 0 && <tr><td colSpan={9} className="px-3 py-6 text-center text-gray-500">{t('admin.taxRules.none')}</td></tr>}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
