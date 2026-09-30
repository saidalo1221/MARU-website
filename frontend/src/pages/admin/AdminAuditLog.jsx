import { useEffect, useState } from 'react'
import { adminListAuditLogs } from '../../api/admin'
import { errorMessage } from '../../api/client'
import { useLocale } from '../../context/LocaleContext'

export default function AdminAuditLog() {
  const { t } = useLocale()
  const [logs, setLogs] = useState([])
  const [entityFilter, setEntityFilter] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    setLoading(true)
    adminListAuditLogs(entityFilter || undefined)
      .then(setLogs)
      .catch((err) => setError(errorMessage(err, t('admin.auditLog.loadFailed'))))
      .finally(() => setLoading(false))
  }, [entityFilter]) // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-2xl font-bold">{t('admin.auditLog.title')}</h1>
        <input value={entityFilter} onChange={(e) => setEntityFilter(e.target.value)} placeholder={t('admin.auditLog.filterPlaceholder')} aria-label={t('admin.auditLog.filterPlaceholder')} className="border border-gray-300 rounded px-2 py-1.5 text-sm" />
      </div>

      {loading && <p>{t('admin.common.loading')}</p>}
      {error && <p role="alert" className="text-red-600 text-sm mb-3">{error}</p>}

      {!loading && (
        <ul className="divide-y divide-gray-100 border border-gray-200 rounded-lg">
          {logs.map((l) => (
            <li key={l.id} className="px-3 py-2 text-sm">
              <span className="font-medium">{l.action}</span> on {l.entity} #{l.entity_id ?? '—'}
              {l.user_id != null && <span className="text-gray-400"> · {t('admin.auditLog.byUser', { id: l.user_id })}</span>}
              <span className="text-gray-400"> · {new Date(l.created_at).toLocaleString()}</span>
              {(l.old_value || l.new_value) && (
                <p className="text-xs text-gray-500 mt-1">
                  {l.old_value ? t('admin.auditLog.before', { value: l.old_value }) : ''}{l.old_value && l.new_value ? ' → ' : ''}{l.new_value ? t('admin.auditLog.after', { value: l.new_value }) : ''}
                </p>
              )}
            </li>
          ))}
          {logs.length === 0 && <li className="px-3 py-6 text-center text-gray-400">{t('admin.auditLog.none')}</li>}
        </ul>
      )}
    </div>
  )
}
