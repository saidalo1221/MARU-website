import { useEffect, useState } from 'react'
import { adminListReviews, adminModerateReview } from '../../api/admin'
import { apiRequest, errorMessage } from '../../api/client'
import { useLocale } from '../../context/LocaleContext'
import Pagination from '../../components/ui/Pagination'
import { PAGE_SIZE } from '../../api/client'

const STATUSES = ['pending', 'approved', 'rejected']

export default function AdminReviews() {
  const { t } = useLocale()
  const [reviews, setReviews] = useState([])
  const [statusFilter, setStatusFilter] = useState('pending')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)

  const load = () => {
    setLoading(true)
    setError(null)
    return adminListReviews(statusFilter || undefined, page)
      .then(({ data, total: n }) => {
        setReviews(data)
        setTotal(n)
      })
      .catch((err) => setError(errorMessage(err, t('admin.reviews.loadFailed'))))
      .finally(() => setLoading(false))
  }

  useEffect(() => setPage(1), [statusFilter])
  useEffect(() => { load() }, [statusFilter, page]) // eslint-disable-line react-hooks/exhaustive-deps

  const remove = async (id) => {
    if (!window.confirm(t('admin.reviews.confirmDelete'))) return
    await apiRequest(`/admin/reviews/${id}`, { method: 'DELETE' })
    await load()
  }

  const moderate = async (id, status) => {
    await adminModerateReview(id, status)
    await load()
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-2xl font-bold">{t('admin.reviews.title')}</h1>
        <select value={statusFilter} aria-label={t('admin.common.status')} onChange={(e) => setStatusFilter(e.target.value)} className="border border-gray-300 rounded px-2 py-1.5 text-sm">
          <option value="">{t('admin.common.allStatuses')}</option>
          {STATUSES.map((s) => <option key={s} value={s}>{s}</option>)}
        </select>
      </div>

      {loading && <p>{t('admin.common.loading')}</p>}
      {error && <p role="alert" className="text-red-600 text-sm">{error}</p>}

      {!loading && !error && (
        <ul className="space-y-3">
          {reviews.map((r) => (
            <li key={r.id} className="border border-gray-200 rounded-lg p-4">
              <div className="flex justify-between items-start">
                <div>
                  <p className="text-yellow-500 text-sm">{'★'.repeat(r.rating)}{'☆'.repeat(5 - r.rating)}</p>
                  <p className="text-sm text-gray-700 mt-1">{r.content || <span className="text-gray-500">{t('admin.reviews.noComment')}</span>}</p>
                  {r.image_urls?.length > 0 && (
                    <div className="flex gap-2 mt-2">
                      {r.image_urls.map((u) => <a key={u} href={u} target="_blank" rel="noopener noreferrer"><img src={u} alt="" loading="lazy" className="h-16 w-16 object-cover rounded border border-gray-200" /></a>)}
                    </div>
                  )}
                  <p className="text-xs text-gray-500 mt-1">{t('admin.reviews.product', { id: r.product_id })} · {r.status}</p>
                </div>
                {r.status !== 'approved' && (
                  <button onClick={() => moderate(r.id, 'approved')} className="text-green-700 text-sm">{t('admin.reviews.approve')}</button>
                )}
              </div>
              {r.status !== 'rejected' && (
                <button onClick={() => moderate(r.id, 'rejected')} className="text-red-600 text-sm mt-2">{t('admin.reviews.reject')}</button>
              )}
              <button onClick={() => remove(r.id)} className="text-red-600 text-sm mt-2 ml-4">{t('admin.reviews.delete')}</button>
            </li>
          ))}
          {reviews.length === 0 && <li className="text-gray-500 text-center py-6">{t('admin.reviews.none')}</li>}
        </ul>
      )}
      <Pagination page={page} pageCount={Math.max(1, Math.ceil(total / PAGE_SIZE))} onChange={setPage} />
    </div>
  )
}
