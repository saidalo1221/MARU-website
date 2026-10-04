import { useEffect, useState } from 'react'
import { apiRequest, errorMessage, PAGE_SIZE } from '../../api/client'
import { useLocale } from '../../context/LocaleContext'
import Pagination from '../../components/ui/Pagination'
import { formatDate } from '../../lib/format'

const TYPES = ['retail', 'wholesale', 'distributor', 'export', 'special']

export default function AdminCustomers() {
  const { t } = useLocale()
  const [rows, setRows] = useState([])
  const [q, setQ] = useState('')
  const [typeFilter, setTypeFilter] = useState('')
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const load = () => {
    const params = new URLSearchParams()
    if (q.trim()) params.set('q', q.trim())
    if (typeFilter) params.set('customer_type', typeFilter)
    if (page > 1) params.set('page', String(page))
    setError(null)
    return apiRequest(`/admin/customers/${params.toString() ? `?${params}` : ''}`, { meta: true })
      .then(({ data, total: n }) => { setRows(data); setTotal(n) })
      .catch((err) => setError(errorMessage(err, t('admin.customers.loadFailed'))))
      .finally(() => setLoading(false))
  }

  useEffect(() => setPage(1), [q, typeFilter])
  useEffect(() => {
    const id = setTimeout(load, q ? 250 : 0) // small debounce while typing
    return () => clearTimeout(id)
  }, [q, typeFilter, page]) // eslint-disable-line react-hooks/exhaustive-deps

  const patch = async (id, body) => {
    setError(null)
    try {
      await apiRequest(`/admin/customers/${id}`, { method: 'PATCH', body })
      await load()
    } catch (err) {
      setError(errorMessage(err, t('admin.customers.saveFailed')))
    }
  }

  return (
    <div>
      <h1 className="text-2xl font-bold mb-1">{t('admin.customers.title')}</h1>
      <p className="text-sm text-gray-500 mb-4">{t('admin.customers.typeHint')}</p>
      <div className="flex flex-wrap gap-2 mb-4">
        <input type="search" value={q} onChange={(e) => setQ(e.target.value)} placeholder={t('admin.customers.search')} aria-label={t('admin.customers.search')} className="flex-1 min-w-[14rem] border border-gray-300 rounded px-3 py-1.5 text-sm" />
        <select value={typeFilter} onChange={(e) => setTypeFilter(e.target.value)} aria-label={t('admin.customers.type')} className="border border-gray-300 rounded px-2 py-1.5 text-sm">
          <option value="">{t('admin.customers.allTypes')}</option>
          {TYPES.map((x) => <option key={x} value={x}>{t(`admin.customers.type_${x}`)}</option>)}
        </select>
      </div>

      {loading && <p>{t('admin.common.loading')}</p>}
      {error && <p role="alert" className="text-red-600 text-sm mb-3">{error}</p>}

      {!loading && (
        <div className="border border-gray-200 rounded-lg overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-left">
              <tr>
                <th scope="col" className="px-3 py-2">{t('admin.customers.customer')}</th>
                <th scope="col" className="px-3 py-2">{t('admin.customers.type')}</th>
                <th scope="col" className="px-3 py-2">{t('admin.customers.ordersCount')}</th>
                <th scope="col" className="px-3 py-2">{t('admin.customers.lastOrder')}</th>
                <th scope="col" className="px-3 py-2">{t('admin.customers.active')}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {rows.map((c) => (
                <tr key={c.id} className="hover:bg-gray-50">
                  <td className="px-3 py-2">
                    <span className="font-medium">{[c.first_name, c.last_name].filter(Boolean).join(' ') || '—'}</span>
                    <span className="block text-xs text-gray-500">{c.email}{c.phone ? ` · ${c.phone}` : ''}</span>
                  </td>
                  <td className="px-3 py-2">
                    <select value={c.customer_type} aria-label={`${t('admin.customers.type')}: ${c.email}`} onChange={(e) => patch(c.id, { customer_type: e.target.value })} className="border border-gray-300 rounded px-2 py-1 text-sm">
                      {TYPES.map((x) => <option key={x} value={x}>{t(`admin.customers.type_${x}`)}</option>)}
                    </select>
                  </td>
                  <td className="px-3 py-2">{c.order_count}</td>
                  <td className="px-3 py-2 text-gray-500">{c.last_order_at ? formatDate(c.last_order_at) : '—'}</td>
                  <td className="px-3 py-2">
                    <input type="checkbox" checked={c.is_active} aria-label={`${t('admin.customers.active')}: ${c.email}`} onChange={(e) => patch(c.id, { is_active: e.target.checked })} />
                  </td>
                </tr>
              ))}
              {rows.length === 0 && <tr><td colSpan={5} className="px-3 py-6 text-center text-gray-500">{t('admin.customers.none')}</td></tr>}
            </tbody>
          </table>
        </div>
      )}
      <Pagination page={page} pageCount={Math.max(1, Math.ceil(total / PAGE_SIZE))} onChange={setPage} />
    </div>
  )
}
