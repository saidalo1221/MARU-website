import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { adminListQuotes } from '../../api/admin'
import { errorMessage } from '../../api/client'
import { useLocale } from '../../context/LocaleContext'
import Pagination from '../../components/ui/Pagination'
import { PAGE_SIZE } from '../../api/client'

const STATUSES = ['new', 'in_review', 'offered', 'accepted', 'rejected', 'expired']

export default function AdminQuotes() {
  const { t } = useLocale()
  const [quotes, setQuotes] = useState([])
  const [statusFilter, setStatusFilter] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)

  useEffect(() => setPage(1), [statusFilter])
  useEffect(() => {
    setLoading(true)
    setError(null)
    adminListQuotes(statusFilter || undefined, page)
      .then(({ data, total: n }) => {
        setQuotes(data)
        setTotal(n)
      })
      .catch((err) => setError(errorMessage(err, t('admin.quotes.loadFailed'))))
      .finally(() => setLoading(false))
  }, [statusFilter, page]) // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-2xl font-bold">{t('admin.quotes.title')}</h1>
        <select value={statusFilter} aria-label={t('admin.common.status')} onChange={(e) => setStatusFilter(e.target.value)} className="border border-gray-300 rounded px-2 py-1.5 text-sm">
          <option value="">{t('admin.common.allStatuses')}</option>
          {STATUSES.map((s) => <option key={s} value={s}>{s}</option>)}
        </select>
      </div>

      {loading && <p>{t('admin.common.loading')}</p>}
      {error && <p role="alert" className="text-red-600 text-sm">{error}</p>}

      {!loading && !error && (
        <div className="border border-gray-200 rounded-lg overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-left">
              <tr>
                <th scope="col" className="px-3 py-2">{t('admin.quotes.rfqNumber')}</th>
                <th scope="col" className="px-3 py-2">{t('admin.quotes.type')}</th>
                <th scope="col" className="px-3 py-2">{t('admin.quotes.name')}</th>
                <th scope="col" className="px-3 py-2">{t('admin.quotes.country')}</th>
                <th scope="col" className="px-3 py-2">{t('admin.common.status')}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {quotes.map((q) => (
                <tr key={q.id} className="hover:bg-gray-50">
                  <td className="px-3 py-2">
                    <Link to={`/admin/quotes/${q.id}`} className="text-brand font-medium">{q.rfq_number ?? `#${q.id}`}</Link>
                  </td>
                  <td className="px-3 py-2">{q.request_type}</td>
                  <td className="px-3 py-2">{q.name}</td>
                  <td className="px-3 py-2">{q.country}</td>
                  <td className="px-3 py-2">{q.status}</td>
                </tr>
              ))}
              {quotes.length === 0 && (
                <tr><td colSpan={5} className="px-3 py-6 text-center text-gray-500">{t('admin.quotes.none')}</td></tr>
              )}
            </tbody>
          </table>
        </div>
      )}
      <Pagination page={page} pageCount={Math.max(1, Math.ceil(total / PAGE_SIZE))} onChange={setPage} />
    </div>
  )
}
