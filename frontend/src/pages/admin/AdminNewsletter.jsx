import { useEffect, useState } from 'react'
import { adminListNewsletter } from '../../api/admin'
import { errorMessage } from '../../api/client'
import { useLocale } from '../../context/LocaleContext'
import { formatDateTime } from '../../lib/format'

const STATUSES = ['', 'confirmed', 'pending', 'unsubscribed']

export default function AdminNewsletter() {
  const { t } = useLocale()
  const [data, setData] = useState({ counts: {}, subscribers: [] })
  const [statusFilter, setStatusFilter] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

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
