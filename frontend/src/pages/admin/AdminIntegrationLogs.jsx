import { useEffect, useState } from 'react'
import { adminIntegrationHealth, adminListIntegrationLogs, adminRetryIntegrationLog } from '../../api/admin'
import { errorMessage } from '../../api/client'
import { useLocale } from '../../context/LocaleContext'

const STATUSES = ['success', 'failed', 'dead_letter']
const HEALTH_STYLE = {
  HEALTHY: 'bg-green-50 text-green-800 border-green-200',
  DEGRADED: 'bg-yellow-50 text-yellow-800 border-yellow-200',
  FAILED: 'bg-red-50 text-red-800 border-red-200',
  DISABLED: 'bg-gray-50 text-gray-600 border-gray-200',
}

export default function AdminIntegrationLogs() {
  const { t } = useLocale()
  const [logs, setLogs] = useState([])
  const [statusFilter, setStatusFilter] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [retryingId, setRetryingId] = useState(null)
  const [health, setHealth] = useState([])

  const load = () => {
    setLoading(true)
    setError(null)
    adminIntegrationHealth().then(setHealth).catch(() => setHealth([]))
    return adminListIntegrationLogs(statusFilter || undefined)
      .then(setLogs)
      .catch((err) => setError(errorMessage(err, t('admin.integrationLogs.loadFailed'))))
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [statusFilter]) // eslint-disable-line react-hooks/exhaustive-deps

  const retry = async (id) => {
    setRetryingId(id)
    try {
      await adminRetryIntegrationLog(id)
      await load()
    } catch (err) {
      setError(errorMessage(err, t('admin.integrationLogs.retryFailed')))
    } finally {
      setRetryingId(null)
    }
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-2xl font-bold">{t('admin.integrationLogs.title')}</h1>
        <select value={statusFilter} aria-label={t('admin.common.status')} onChange={(e) => setStatusFilter(e.target.value)} className="border border-gray-300 rounded px-2 py-1.5 text-sm">
          <option value="">{t('admin.common.allStatuses')}</option>
          {STATUSES.map((s) => <option key={s} value={s}>{s}</option>)}
        </select>
      </div>

      {health.length > 0 && (
        <section aria-label={t('admin.integrationLogs.healthTitle')} className="mb-4">
          <h2 className="text-sm font-semibold mb-2">{t('admin.integrationLogs.healthTitle')}</h2>
          <ul className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
            {health.map((h) => (
              <li key={h.integration} className={`border rounded-lg p-3 text-sm ${HEALTH_STYLE[h.status] || HEALTH_STYLE.DISABLED}`}>
                <div className="flex justify-between font-medium">
                  <span>{h.integration}</span>
                  <span>{t(`admin.integrationLogs.health.${h.status}`)}</span>
                </div>
                <p className="text-xs mt-1">
                  {h.success_24h} {t('admin.integrationLogs.healthSuccess')} · {h.failed_24h} {t('admin.integrationLogs.healthFailed')} · {h.dead_letter_24h} {t('admin.integrationLogs.healthDead')}
                </p>
              </li>
            ))}
          </ul>
        </section>
      )}

      {loading && <p>{t('admin.common.loading')}</p>}
      {error && <p role="alert" className="text-red-600 text-sm mb-3">{error}</p>}

      {!loading && (
        <div className="border border-gray-200 rounded-lg overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-left">
              <tr>
                <th scope="col" className="px-3 py-2">{t('admin.integrationLogs.integration')}</th>
                <th scope="col" className="px-3 py-2">{t('admin.integrationLogs.operation')}</th>
                <th scope="col" className="px-3 py-2">{t('admin.integrationLogs.entity')}</th>
                <th scope="col" className="px-3 py-2">{t('admin.common.status')}</th>
                <th scope="col" className="px-3 py-2">{t('admin.integrationLogs.attempt')}</th>
                <th scope="col" className="px-3 py-2">{t('admin.integrationLogs.error')}</th>
                <th scope="col" className="px-3 py-2"><span className="sr-only">{t('admin.common.actions')}</span></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {logs.map((l) => (
                <tr key={l.id} className="hover:bg-gray-50">
                  <td className="px-3 py-2">{l.integration}</td>
                  <td className="px-3 py-2">{l.operation}</td>
                  <td className="px-3 py-2">{l.internal_entity} #{l.internal_id}</td>
                  <td className="px-3 py-2">{l.status}</td>
                  <td className="px-3 py-2">{l.attempt}</td>
                  <td className="px-3 py-2 text-red-600 max-w-xs truncate" title={l.error_message || ''}>{l.error_message || '—'}</td>
                  <td className="px-3 py-2 text-right">
                    {l.status !== 'success' && (
                      <button onClick={() => retry(l.id)} disabled={retryingId === l.id} className="text-brand disabled:opacity-40">
                        {retryingId === l.id ? t('admin.integrationLogs.retrying') : t('admin.integrationLogs.retry')}
                      </button>
                    )}
                  </td>
                </tr>
              ))}
              {logs.length === 0 && <tr><td colSpan={7} className="px-3 py-6 text-center text-gray-500">{t('admin.integrationLogs.none')}</td></tr>}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
