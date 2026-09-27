import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { adminListQuotes } from '../../api/admin'
import { errorMessage } from '../../api/client'

const STATUSES = ['new', 'in_review', 'offered', 'accepted', 'rejected', 'expired']

export default function AdminQuotes() {
  const [quotes, setQuotes] = useState([])
  const [statusFilter, setStatusFilter] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    setLoading(true)
    setError(null)
    adminListQuotes(statusFilter || undefined)
      .then(setQuotes)
      .catch((err) => setError(errorMessage(err, 'Failed to load quotes')))
      .finally(() => setLoading(false))
  }, [statusFilter])

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-2xl font-bold">Quotes</h1>
        <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} className="border border-gray-300 rounded px-2 py-1.5 text-sm">
          <option value="">All statuses</option>
          {STATUSES.map((s) => <option key={s} value={s}>{s}</option>)}
        </select>
      </div>

      {loading && <p>Loading...</p>}
      {error && <p className="text-red-600 text-sm">{error}</p>}

      {!loading && !error && (
        <div className="border border-gray-200 rounded-lg overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-left">
              <tr>
                <th className="px-3 py-2">RFQ #</th>
                <th className="px-3 py-2">Type</th>
                <th className="px-3 py-2">Name</th>
                <th className="px-3 py-2">Country</th>
                <th className="px-3 py-2">Status</th>
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
                <tr><td colSpan={5} className="px-3 py-6 text-center text-gray-400">No quotes found.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
