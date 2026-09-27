import { useEffect, useState } from 'react'
import { adminListReviews, adminModerateReview } from '../../api/admin'
import { errorMessage } from '../../api/client'

const STATUSES = ['pending', 'approved', 'rejected']

export default function AdminReviews() {
  const [reviews, setReviews] = useState([])
  const [statusFilter, setStatusFilter] = useState('pending')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const load = () => {
    setLoading(true)
    setError(null)
    return adminListReviews(statusFilter || undefined)
      .then(setReviews)
      .catch((err) => setError(errorMessage(err, 'Failed to load reviews')))
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [statusFilter]) // eslint-disable-line react-hooks/exhaustive-deps

  const moderate = async (id, status) => {
    await adminModerateReview(id, status)
    await load()
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-2xl font-bold">Reviews</h1>
        <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} className="border border-gray-300 rounded px-2 py-1.5 text-sm">
          <option value="">All statuses</option>
          {STATUSES.map((s) => <option key={s} value={s}>{s}</option>)}
        </select>
      </div>

      {loading && <p>Loading...</p>}
      {error && <p className="text-red-600 text-sm">{error}</p>}

      {!loading && !error && (
        <ul className="space-y-3">
          {reviews.map((r) => (
            <li key={r.id} className="border border-gray-200 rounded-lg p-4">
              <div className="flex justify-between items-start">
                <div>
                  <p className="text-yellow-500 text-sm">{'★'.repeat(r.rating)}{'☆'.repeat(5 - r.rating)}</p>
                  <p className="text-sm text-gray-700 mt-1">{r.content || <span className="text-gray-400">No comment</span>}</p>
                  <p className="text-xs text-gray-400 mt-1">Product #{r.product_id} · {r.status}</p>
                </div>
                {r.status !== 'approved' && (
                  <button onClick={() => moderate(r.id, 'approved')} className="text-green-600 text-sm">Approve</button>
                )}
              </div>
              {r.status !== 'rejected' && (
                <button onClick={() => moderate(r.id, 'rejected')} className="text-red-500 text-sm mt-2">Reject</button>
              )}
            </li>
          ))}
          {reviews.length === 0 && <p className="text-gray-400 text-center py-6">No reviews found.</p>}
        </ul>
      )}
    </div>
  )
}
