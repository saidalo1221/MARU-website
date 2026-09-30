import { useEffect, useState } from 'react'
import { adminCreateWarehouse, adminListWarehouses, adminUpdateWarehouse } from '../../api/admin'
import { errorMessage } from '../../api/client'
import { useLocale } from '../../context/LocaleContext'
import MapPicker from '../../components/MapPicker'

const emptyForm = { name: '', country: '', address: '', latitude: null, longitude: null, priority: 100, is_active: true }

export default function AdminWarehouses() {
  const { t } = useLocale()
  const [warehouses, setWarehouses] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [editingId, setEditingId] = useState(null)
  const [form, setForm] = useState(emptyForm)
  const [formOpen, setFormOpen] = useState(false)
  const [formError, setFormError] = useState(null)
  const [submitting, setSubmitting] = useState(false)

  const load = () => adminListWarehouses().then(setWarehouses).catch((err) => setError(errorMessage(err, t('admin.warehouses.loadFailed')))).finally(() => setLoading(false))

  useEffect(() => { load() }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const update = (field) => (e) => {
    const value = e.target.type === 'checkbox' ? e.target.checked : e.target.value
    setForm((f) => ({ ...f, [field]: value }))
  }

  const openNew = () => { setEditingId(null); setForm(emptyForm); setFormError(null); setFormOpen(true) }
  const openEdit = (w) => {
    setEditingId(w.id)
    setForm({
      name: w.name,
      country: w.country,
      address: w.address || '',
      latitude: w.latitude,
      longitude: w.longitude,
      priority: w.priority,
      is_active: w.is_active,
    })
    setFormError(null)
    setFormOpen(true)
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setFormError(null)
    setSubmitting(true)
    try {
      const payload = { ...form, priority: Number(form.priority) }
      if (editingId) await adminUpdateWarehouse(editingId, payload)
      else await adminCreateWarehouse(payload)
      setFormOpen(false)
      await load()
    } catch (err) {
      setFormError(errorMessage(err, t('admin.warehouses.saveFailed')))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-2xl font-bold">{t('admin.warehouses.title')}</h1>
        {!formOpen && <button onClick={openNew} className="bg-brand text-white px-4 py-2 rounded text-sm font-medium">{t('admin.warehouses.add')}</button>}
      </div>

      {loading && <p>{t('admin.common.loading')}</p>}
      {error && <p role="alert" className="text-red-600 text-sm mb-3">{error}</p>}

      {formOpen && (
        <form onSubmit={handleSubmit} className="border border-gray-200 rounded-lg p-4 mb-6 space-y-3">
          <input required placeholder={t('admin.common.name')} aria-label={t('admin.common.name')} value={form.name} onChange={update('name')} className="w-full border border-gray-300 rounded px-3 py-2 text-sm" />
          <input required placeholder={t('admin.common.country')} aria-label={t('admin.common.country')} value={form.country} onChange={update('country')} className="w-full border border-gray-300 rounded px-3 py-2 text-sm" />
          <input placeholder={t('admin.warehouses.address')} aria-label={t('admin.warehouses.address')} value={form.address} onChange={update('address')} className="w-full border border-gray-300 rounded px-3 py-2 text-sm" />
          <div>
            <label className="block text-xs text-gray-500 mb-1">{t('admin.warehouses.location')}</label>
            <MapPicker
              latitude={form.latitude}
              longitude={form.longitude}
              onChange={({ latitude, longitude }) => setForm((f) => ({ ...f, latitude, longitude }))}
              onReverseGeocode={({ country, addressLine }) => {
                setForm((f) => ({
                  ...f,
                  country: country || f.country,
                  address: addressLine || f.address,
                }))
              }}
            />
          </div>
          <div>
            <label className="block text-xs text-gray-500 mb-1">{t('admin.warehouses.priority')}</label>
            <input type="number" min="0" value={form.priority} aria-label={t('admin.warehouses.priority')} onChange={update('priority')} className="w-full border border-gray-300 rounded px-3 py-2 text-sm" />
          </div>
          <label className="flex items-center gap-2 text-sm">
            <input type="checkbox" checked={form.is_active} onChange={update('is_active')} /> {t('admin.common.active')}
          </label>
          {formError && <p role="alert" className="text-sm text-red-600">{formError}</p>}
          <div className="flex gap-2">
            <button type="submit" disabled={submitting} className="bg-brand text-white px-4 py-2 rounded text-sm font-medium disabled:opacity-40">
              {submitting ? t('admin.common.saving') : t('admin.common.save')}
            </button>
            <button type="button" onClick={() => setFormOpen(false)} className="border border-gray-300 rounded px-4 py-2 text-sm">{t('admin.common.cancel')}</button>
          </div>
        </form>
      )}

      {!loading && (
        <div className="border border-gray-200 rounded-lg overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-left">
              <tr>
                <th className="px-3 py-2">{t('admin.common.name')}</th>
                <th className="px-3 py-2">{t('admin.common.country')}</th>
                <th className="px-3 py-2">{t('admin.warehouses.priority')}</th>
                <th className="px-3 py-2">{t('admin.common.active')}</th>
                <th className="px-3 py-2"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {warehouses.map((w) => (
                <tr key={w.id} className="hover:bg-gray-50">
                  <td className="px-3 py-2">{w.name}</td>
                  <td className="px-3 py-2">{w.country}</td>
                  <td className="px-3 py-2">{w.priority}</td>
                  <td className="px-3 py-2">{w.is_active ? t('admin.common.yes') : t('admin.common.no')}</td>
                  <td className="px-3 py-2 text-right"><button onClick={() => openEdit(w)} className="text-brand">{t('admin.common.edit')}</button></td>
                </tr>
              ))}
              {warehouses.length === 0 && <tr><td colSpan={5} className="px-3 py-6 text-center text-gray-400">{t('admin.warehouses.none')}</td></tr>}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
