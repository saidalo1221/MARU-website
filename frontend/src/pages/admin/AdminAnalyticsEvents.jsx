import { useEffect, useState } from 'react'
import { adminListAnalyticsEvents } from '../../api/admin'
import { errorMessage } from '../../api/client'
import { useLocale } from '../../context/LocaleContext'

export default function AdminAnalyticsEvents() {
  const { t } = useLocale()
  const [events, setEvents] = useState([])
  const [eventFilter, setEventFilter] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    setLoading(true)
    adminListAnalyticsEvents(eventFilter || undefined)
      .then(setEvents)
      .catch((err) => setError(errorMessage(err, t('admin.analyticsEvents.loadFailed'))))
      .finally(() => setLoading(false))
  }, [eventFilter]) // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-2xl font-bold">{t('admin.analyticsEvents.title')}</h1>
        <input value={eventFilter} onChange={(e) => setEventFilter(e.target.value)} placeholder={t('admin.analyticsEvents.filterPlaceholder')} aria-label={t('admin.analyticsEvents.filterPlaceholder')} className="border border-gray-300 rounded px-2 py-1.5 text-sm" />
      </div>

      {loading && <p>{t('admin.common.loading')}</p>}
      {error && <p role="alert" className="text-red-600 text-sm mb-3">{error}</p>}

      {!loading && (
        <div className="border border-gray-200 rounded-lg overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-left">
              <tr>
                <th className="px-3 py-2">{t('admin.analyticsEvents.event')}</th>
                <th className="px-3 py-2">{t('admin.analyticsEvents.user')}</th>
                <th className="px-3 py-2">{t('admin.analyticsEvents.properties')}</th>
                <th className="px-3 py-2">{t('admin.analyticsEvents.when')}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {events.map((e) => (
                <tr key={e.id} className="hover:bg-gray-50">
                  <td className="px-3 py-2 font-medium">{e.event_name}</td>
                  <td className="px-3 py-2 text-gray-500">{e.user_id ?? t('admin.analyticsEvents.guest')}</td>
                  <td className="px-3 py-2 max-w-sm truncate" title={e.properties || ''}>{e.properties || '—'}</td>
                  <td className="px-3 py-2 text-gray-500">{new Date(e.created_at).toLocaleString()}</td>
                </tr>
              ))}
              {events.length === 0 && <tr><td colSpan={4} className="px-3 py-6 text-center text-gray-400">{t('admin.analyticsEvents.none')}</td></tr>}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
