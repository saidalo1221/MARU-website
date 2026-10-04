import { useEffect, useState } from 'react'
import { adminListCampaigns, adminListNewsletter, adminSendCampaign, adminTestCampaign } from '../../api/admin'
import { errorMessage } from '../../api/client'
import { useLocale } from '../../context/LocaleContext'
import { formatDateTime } from '../../lib/format'

const STATUSES = ['', 'confirmed', 'pending', 'unsubscribed']

function Compose({ confirmed, onSent }) {
  const { t } = useLocale()
  const [form, setForm] = useState({ subject: '', body: '', locale: '' })
  const [busy, setBusy] = useState(false)
  const [msg, setMsg] = useState(null)
  const payload = () => ({ subject: form.subject, body: form.body, locale: form.locale || null })
  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }))

  const run = async (fn, okText) => {
    setBusy(true)
    setMsg(null)
    try {
      const res = await fn()
      setMsg({ ok: true, text: okText(res) })
      return res
    } catch (err) {
      setMsg({ ok: false, text: errorMessage(err, t('admin.newsletter.sendFailed')) })
    } finally {
      setBusy(false)
    }
  }
  const test = (e) => {
    e.preventDefault()
    run(() => adminTestCampaign(payload()), (r) => t('admin.newsletter.testSent', { email: r.sent_to }))
  }
  const send = async () => {
    if (!window.confirm(t('admin.newsletter.confirmSend', { n: confirmed }))) return
    const res = await run(() => adminSendCampaign(payload()), (r) => t('admin.newsletter.sentOk', { n: r.recipients_total }))
    if (res) onSent()
  }
  const field = 'border border-gray-300 rounded px-2 py-1.5 text-sm w-full'
  return (
    <form onSubmit={test} className="border border-gray-200 rounded-lg p-4 mb-6 space-y-3">
      <h2 className="font-semibold">{t('admin.newsletter.composeTitle')}</h2>
      <p className="text-xs text-gray-500">{t('admin.newsletter.composeHint')}</p>
      <label className="block text-xs text-gray-500">{t('admin.newsletter.subject')}
        <input required maxLength={200} value={form.subject} onChange={set('subject')} className={field} />
      </label>
      <label className="block text-xs text-gray-500">{t('admin.newsletter.body')}
        <textarea required rows={8} maxLength={20000} value={form.body} onChange={set('body')} className={field} />
      </label>
      <label className="block text-xs text-gray-500">{t('admin.newsletter.language')}
        <select value={form.locale} onChange={set('locale')} className="border border-gray-300 rounded px-2 py-1.5 text-sm block">
          <option value="">{t('admin.newsletter.allLanguages')}</option>
          {['ru', 'uz', 'en'].map((l) => <option key={l} value={l}>{l.toUpperCase()}</option>)}
        </select>
      </label>
      <div className="flex flex-wrap gap-2">
        <button type="submit" disabled={busy} className="border border-gray-300 rounded px-3 py-1.5 text-sm">{t('admin.newsletter.test')}</button>
        <button type="button" disabled={busy || !form.subject.trim() || !form.body.trim()} onClick={send} className="bg-brand text-white rounded px-3 py-1.5 text-sm disabled:opacity-50">{busy ? t('admin.newsletter.sending') : t('admin.newsletter.send')}</button>
      </div>
      {msg && <p role={msg.ok ? 'status' : 'alert'} className={`text-sm ${msg.ok ? 'text-green-700' : 'text-red-600'}`}>{msg.text}</p>}
    </form>
  )
}

function Campaigns({ rows }) {
  const { t } = useLocale()
  return (
    <section className="mb-6">
      <h2 className="font-semibold mb-2">{t('admin.newsletter.campaigns')}</h2>
      {rows.length === 0 ? <p className="text-sm text-gray-500">{t('admin.newsletter.noCampaigns')}</p> : (
        <table className="w-full text-sm border border-gray-200 rounded">
          <thead className="bg-gray-50 text-left">
            <tr>
              <th scope="col" className="px-3 py-1.5">{t('admin.newsletter.subject')}</th>
              <th scope="col" className="px-3 py-1.5">{t('admin.newsletter.recipients')}</th>
              <th scope="col" className="px-3 py-1.5">{t('admin.newsletter.sentCol')}</th>
              <th scope="col" className="px-3 py-1.5">{t('admin.newsletter.failedCol')}</th>
              <th scope="col" className="px-3 py-1.5">{t('admin.newsletter.waitingCol')}</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {rows.map((c) => (
              <tr key={c.id}><td className="px-3 py-1.5">{c.subject}</td><td className="px-3 py-1.5">{c.recipients_total}</td><td className="px-3 py-1.5">{c.sent}</td><td className="px-3 py-1.5">{c.failed}</td><td className="px-3 py-1.5">{c.waiting}</td></tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  )
}

export default function AdminNewsletter() {
  const { t } = useLocale()
  const [data, setData] = useState({ counts: {}, subscribers: [] })
  const [statusFilter, setStatusFilter] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [campaigns, setCampaigns] = useState([])
  const loadCampaigns = () => adminListCampaigns().then(setCampaigns).catch(() => setCampaigns([]))
  useEffect(() => { loadCampaigns() }, [])

  useEffect(() => {
    setLoading(true)
    adminListNewsletter(statusFilter || undefined)
      .then(setData)
      .catch((err) => setError(errorMessage(err, t('admin.newsletter.loadFailed'))))
      .finally(() => setLoading(false))
  }, [statusFilter]) // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div>
      <div className="flex items-center justify-between mb-2">
        <h1 className="text-2xl font-bold">{t('admin.newsletter.title')}</h1>
        <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} aria-label={t('admin.newsletter.status')} className="border border-gray-300 rounded px-2 py-1.5 text-sm">
          {STATUSES.map((s) => <option key={s} value={s}>{s ? t(`admin.newsletter.${s}`) : t('admin.newsletter.all')}</option>)}
        </select>
      </div>
      <p className="text-sm text-gray-500 mb-4">
        {['confirmed', 'pending', 'unsubscribed'].map((s) => `${t(`admin.newsletter.${s}`)}: ${data.counts[s] || 0}`).join(' · ')}
      </p>

      <Compose confirmed={data.counts.confirmed || 0} onSent={loadCampaigns} />
      <Campaigns rows={campaigns} />

      {loading && <p>{t('admin.common.loading')}</p>}
      {error && <p role="alert" className="text-red-600 text-sm mb-3">{error}</p>}

      {!loading && (
        <div className="border border-gray-200 rounded-lg overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-left">
              <tr>
                <th scope="col" className="px-3 py-2">{t('admin.newsletter.email')}</th>
                <th scope="col" className="px-3 py-2">{t('admin.newsletter.status')}</th>
                <th scope="col" className="px-3 py-2">{t('admin.newsletter.language')}</th>
                <th scope="col" className="px-3 py-2">{t('admin.newsletter.signedUp')}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {data.subscribers.map((s) => (
                <tr key={s.id} className="hover:bg-gray-50">
                  <td className="px-3 py-2">{s.email}</td>
                  <td className="px-3 py-2">{t(`admin.newsletter.${s.status}`)}</td>
                  <td className="px-3 py-2 uppercase">{s.locale}</td>
                  <td className="px-3 py-2 text-gray-500">{formatDateTime(s.created_at)}</td>
                </tr>
              ))}
              {data.subscribers.length === 0 && <tr><td colSpan={4} className="px-3 py-6 text-center text-gray-500">{t('admin.newsletter.none')}</td></tr>}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
