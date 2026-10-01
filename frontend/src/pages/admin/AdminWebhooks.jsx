import { useEffect, useState } from 'react'
import { apiRequest, errorMessage } from '../../api/client'
import { useLocale } from '../../context/LocaleContext'
import { formatDateTime } from '../../lib/format'

export default function AdminWebhooks() {
  const { t } = useLocale()
  const [rows, setRows] = useState([])
  const [events, setEvents] = useState([])
  const [form, setForm] = useState({ url: '', description: '', all: true, selected: [] })
  const [secret, setSecret] = useState(null)
  const [error, setError] = useState(null)
  const [note, setNote] = useState(null)
  const [loading, setLoading] = useState(true)

  const load = () =>
    apiRequest('/admin/webhooks/')
      .then(setRows)
      .catch((err) => setError(errorMessage(err, t('admin.webhooks.loadFailed'))))
      .finally(() => setLoading(false))
  useEffect(() => {
    load()
    apiRequest('/admin/webhooks/events').then(setEvents).catch(() => {})
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const create = async (e) => {
    e.preventDefault()
    setError(null)
    try {
      const created = await apiRequest('/admin/webhooks/', {
        method: 'POST',
        body: { url: form.url.trim(), description: form.description.trim() || null, events: form.all ? ['*'] : form.selected },
      })
      setSecret(created.secret)
      setForm({ url: '', description: '', all: true, selected: [] })
      await load()
    } catch (err) {
      setError(errorMessage(err, t('admin.webhooks.saveFailed')))
    }
  }

  const act = async (fn) => {
    setError(null)
    setNote(null)
    try {
      await fn()
      await load()
    } catch (err) {
      setError(errorMessage(err, t('admin.webhooks.saveFailed')))
    }
  }

  return (
    <div>
      <h1 className="text-2xl font-bold mb-1">{t('admin.webhooks.title')}</h1>
      <p className="text-sm text-gray-500 mb-4">{t('admin.webhooks.subtitle')}</p>

      {secret && (
        <div role="status" className="border border-yellow-300 bg-yellow-50 rounded-lg p-3 mb-4 text-sm">
          <p className="font-medium mb-1">{t('admin.webhooks.secretTitle')}</p>
          <code className="block break-all bg-white border border-yellow-200 rounded px-2 py-1 select-all">{secret}</code>
          <p className="text-xs text-gray-600 mt-2">{t('admin.webhooks.secretHint')}</p>
          <button type="button" onClick={() => setSecret(null)} className="text-brand text-xs mt-2">OK</button>
        </div>
      )}

      <form onSubmit={create} className="border border-gray-200 rounded-lg p-4 mb-6 space-y-3">
        <h2 className="font-semibold">{t('admin.webhooks.add')}</h2>
        <input required type="url" placeholder={t('admin.webhooks.url')} aria-label={t('admin.webhooks.url')} value={form.url} onChange={(e) => setForm((f) => ({ ...f, url: e.target.value }))} className="w-full border border-gray-300 rounded px-3 py-2 text-sm" />
        <input placeholder={t('admin.webhooks.description')} aria-label={t('admin.webhooks.description')} maxLength={200} value={form.description} onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))} className="w-full border border-gray-300 rounded px-3 py-2 text-sm" />
        <fieldset>
          <legend className="text-xs text-gray-500 mb-1">{t('admin.webhooks.events')}</legend>
          <label className="flex items-center gap-2 text-sm mb-1"><input type="checkbox" checked={form.all} onChange={(e) => setForm((f) => ({ ...f, all: e.target.checked }))} /> {t('admin.webhooks.allEvents')}</label>
          {!form.all && (
            <div className="grid grid-cols-2 gap-x-3 text-sm">
              {events.map((ev) => (
                <label key={ev} className="flex items-center gap-2">
                  <input type="checkbox" checked={form.selected.includes(ev)} onChange={(e) => setForm((f) => ({ ...f, selected: e.target.checked ? [...f.selected, ev] : f.selected.filter((x) => x !== ev) }))} /> {ev}
                </label>
              ))}
            </div>
          )}
        </fieldset>
        <button type="submit" className="bg-brand text-white rounded px-4 py-2 text-sm font-medium">{t('admin.webhooks.save')}</button>
      </form>

      {loading && <p>{t('admin.common.loading')}</p>}
      {error && <p role="alert" className="text-red-600 text-sm mb-3">{error}</p>}
      {note && <p role="status" className="text-sm text-green-700 mb-3">{note}</p>}

      {!loading && rows.length === 0 && <p className="text-sm text-gray-500">{t('admin.webhooks.none')}</p>}
      <ul className="space-y-3">
        {rows.map((r) => (
          <li key={r.id} className="border border-gray-200 rounded-lg p-3 text-sm">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <span className="font-medium break-all">{r.url}</span>
              <label className="flex items-center gap-1">
                <input type="checkbox" checked={r.is_active} onChange={(e) => act(() => apiRequest(`/admin/webhooks/${r.id}`, { method: 'PATCH', body: { is_active: e.target.checked } }))} /> {t('admin.webhooks.active')}
              </label>
            </div>
            {r.description && <p className="text-gray-500">{r.description}</p>}
            <p className="text-xs text-gray-500 mt-1">{r.events.join(', ')} · {r.secret_hint}</p>
            <p className="text-xs mt-1">
              {t('admin.webhooks.lastDelivery')}: {r.last_delivery_at ? formatDateTime(r.last_delivery_at) : t('admin.webhooks.never')}
              {r.last_status_code ? ` · HTTP ${r.last_status_code}` : ''}
              {r.last_error ? <span className="text-red-600"> · {r.last_error}</span> : null}
            </p>
            <div className="flex flex-wrap gap-3 mt-2">
              <button type="button" onClick={() => act(async () => { await apiRequest(`/admin/webhooks/${r.id}/test`, { method: 'POST' }); setNote(t('admin.webhooks.testQueued')) })} className="text-brand">{t('admin.webhooks.test')}</button>
              <button type="button" onClick={() => act(async () => { const c = await apiRequest(`/admin/webhooks/${r.id}/rotate-secret`, { method: 'POST' }); setSecret(c.secret) })} className="text-brand">{t('admin.webhooks.rotate')}</button>
              <button type="button" onClick={() => { if (window.confirm(t('admin.webhooks.confirmDelete'))) act(() => apiRequest(`/admin/webhooks/${r.id}`, { method: 'DELETE' })) }} className="text-red-600">{t('admin.webhooks.delete')}</button>
            </div>
          </li>
        ))}
      </ul>
    </div>
  )
}
