import { useEffect, useState } from 'react'
import { adminCreateNotificationTemplate, adminListNotificationTemplates, adminUpdateNotificationTemplate } from '../../api/admin'
import { errorMessage } from '../../api/client'
import { useLocale } from '../../context/LocaleContext'

const emptyForm = { event: '', locale: 'en', channel: 'email', subject: '', body: '', is_active: true }

export default function AdminNotificationTemplates() {
  const { t } = useLocale()
  const [templates, setTemplates] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [editingId, setEditingId] = useState(null)
  const [form, setForm] = useState(emptyForm)
  const [formOpen, setFormOpen] = useState(false)
  const [formError, setFormError] = useState(null)
  const [submitting, setSubmitting] = useState(false)

  const load = () => adminListNotificationTemplates().then(setTemplates).catch((err) => setError(errorMessage(err, t('admin.notificationTemplates.loadFailed')))).finally(() => setLoading(false))
  useEffect(() => { load() }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const update = (field) => (e) => {
    const value = e.target.type === 'checkbox' ? e.target.checked : e.target.value
    setForm((f) => ({ ...f, [field]: value }))
  }

  const openNew = () => { setEditingId(null); setForm(emptyForm); setFormError(null); setFormOpen(true) }
  const openEdit = (t2) => {
    setEditingId(t2.id)
    setForm({ event: t2.event, locale: t2.locale, channel: t2.channel, subject: t2.subject || '', body: t2.body, is_active: t2.is_active })
    setFormError(null)
    setFormOpen(true)
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setFormError(null)
    setSubmitting(true)
    try {
      if (editingId) {
        await adminUpdateNotificationTemplate(editingId, { subject: form.subject || null, body: form.body, is_active: form.is_active })
      } else {
        await adminCreateNotificationTemplate({ event: form.event, locale: form.locale, channel: form.channel, subject: form.subject || null, body: form.body, is_active: form.is_active })
      }
      setFormOpen(false)
      await load()
    } catch (err) {
      setFormError(errorMessage(err, t('admin.notificationTemplates.saveFailed')))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-2xl font-bold">{t('admin.notificationTemplates.title')}</h1>
        {!formOpen && <button onClick={openNew} className="bg-brand text-white px-4 py-2 rounded text-sm font-medium">{t('admin.notificationTemplates.add')}</button>}
      </div>

      {loading && <p>{t('admin.common.loading')}</p>}
      {error && <p className="text-red-600 text-sm mb-3">{error}</p>}

      {formOpen && (
        <form onSubmit={handleSubmit} className="border border-gray-200 rounded-lg p-4 mb-6 space-y-3">
          <div className="grid grid-cols-3 gap-3">
            <input required disabled={!!editingId} placeholder={t('admin.notificationTemplates.event')} value={form.event} onChange={update('event')} className="border border-gray-300 rounded px-3 py-2 text-sm disabled:bg-gray-100" />
            <select disabled={!!editingId} value={form.locale} onChange={update('locale')} className="border border-gray-300 rounded px-3 py-2 text-sm disabled:bg-gray-100">
              <option value="en">en</option><option value="ru">ru</option><option value="uz">uz</option>
            </select>
            <input disabled={!!editingId} placeholder={t('admin.notificationTemplates.channel')} value={form.channel} onChange={update('channel')} className="border border-gray-300 rounded px-3 py-2 text-sm disabled:bg-gray-100" />
          </div>
          <input placeholder={t('admin.notificationTemplates.subject')} value={form.subject} onChange={update('subject')} className="w-full border border-gray-300 rounded px-3 py-2 text-sm" />
          <textarea required placeholder={t('admin.notificationTemplates.body')} value={form.body} onChange={update('body')} rows={5} className="w-full border border-gray-300 rounded px-3 py-2 text-sm" />
          <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={form.is_active} onChange={update('is_active')} /> {t('admin.common.active')}</label>
          {formError && <p className="text-sm text-red-600">{formError}</p>}
          <div className="flex gap-2">
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
                <th className="px-3 py-2">{t('admin.notificationTemplates.eventCol')}</th>
                <th className="px-3 py-2">{t('admin.notificationTemplates.locale')}</th>
                <th className="px-3 py-2">{t('admin.notificationTemplates.channel')}</th>
                <th className="px-3 py-2">{t('admin.common.active')}</th>
                <th className="px-3 py-2"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {templates.map((tpl) => (
                <tr key={tpl.id} className="hover:bg-gray-50">
                  <td className="px-3 py-2">{tpl.event}</td>
                  <td className="px-3 py-2">{tpl.locale}</td>
                  <td className="px-3 py-2">{tpl.channel}</td>
                  <td className="px-3 py-2">{tpl.is_active ? t('admin.common.yes') : t('admin.common.no')}</td>
                  <td className="px-3 py-2 text-right"><button onClick={() => openEdit(tpl)} className="text-brand">{t('admin.common.edit')}</button></td>
                </tr>
              ))}
              {templates.length === 0 && <tr><td colSpan={5} className="px-3 py-6 text-center text-gray-400">{t('admin.notificationTemplates.none')}</td></tr>}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
