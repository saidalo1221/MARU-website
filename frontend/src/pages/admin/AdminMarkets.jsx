import { useEffect, useState } from 'react'
import { apiRequest, errorMessage, PAGE_SIZE } from '../../api/client'
import { listShippingCountries } from '../../api/shipping'
import { useLocale } from '../../context/LocaleContext'
import Pagination from '../../components/ui/Pagination'

// Which products are sold in which countries. Pick products, pick countries, apply.
export default function AdminMarkets() {
  const { t } = useLocale()
  const [rows, setRows] = useState([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [q, setQ] = useState('')
  const [restrictedOnly, setRestrictedOnly] = useState(false)
  const [selected, setSelected] = useState(new Set())
  const [known, setKnown] = useState([])
  const [countries, setCountries] = useState([])
  const [extra, setExtra] = useState('')
  const [error, setError] = useState(null)
  const [msg, setMsg] = useState(null)

  const load = () => {
    const params = new URLSearchParams()
    if (q.trim()) params.set('q', q.trim())
    if (restrictedOnly) params.set('restricted_only', 'true')
    if (page > 1) params.set('page', String(page))
    return apiRequest(`/admin/markets/${params.toString() ? `?${params}` : ''}`, { meta: true })
      .then(({ data, total: n }) => { setRows(data); setTotal(n) })
      .catch((err) => setError(errorMessage(err, t('admin.markets.failed'))))
  }

  useEffect(() => { listShippingCountries().then(setKnown).catch(() => {}) }, [])
  useEffect(() => setPage(1), [q, restrictedOnly])
  useEffect(() => {
    const id = setTimeout(load, q ? 250 : 0)
    return () => clearTimeout(id)
  }, [q, restrictedOnly, page]) // eslint-disable-line react-hooks/exhaustive-deps

  const toggleRow = (id) => setSelected((s) => { const n = new Set(s); n.has(id) ? n.delete(id) : n.add(id); return n })
  const allOnPage = rows.length > 0 && rows.every((r) => selected.has(r.id))
  const toggleAll = () => setSelected((s) => { const n = new Set(s); rows.forEach((r) => (allOnPage ? n.delete(r.id) : n.add(r.id))); return n })
  const toggleCountry = (c) => setCountries((l) => (l.includes(c) ? l.filter((x) => x !== c) : [...l, c]))

  const chosen = () => [...new Set([...countries, ...extra.split(',').map((x) => x.trim()).filter(Boolean)])]

  const apply = async (kind) => {
    setError(null)
    setMsg(null)
    const body = { product_ids: [...selected] }
    if (kind === 'sold') Object.assign(body, { set_sold: true, sold_in_countries: chosen() })
    if (kind === 'hidden') Object.assign(body, { set_hidden: true, hidden_in_countries: chosen() })
    if (kind === 'clear') Object.assign(body, { set_sold: true, set_hidden: true, sold_in_countries: [], hidden_in_countries: [] })
    try {
      const r = await apiRequest('/admin/markets/bulk', { method: 'PUT', body })
      setMsg(t('admin.markets.applied', { n: r.updated }))
      await load()
    } catch (err) {
      setError(errorMessage(err, t('admin.markets.failed')))
    }
  }

  const chips = (list) => (list && list.length ? list.join(', ') : '—')
  const none = selected.size === 0
  const needCountries = chosen().length === 0

  return (
    <div>
      <h1 className="text-2xl font-bold mb-1">{t('admin.markets.title')}</h1>
      <p className="text-sm text-gray-500 mb-4">{t('admin.markets.subtitle')}</p>

      <div className="flex flex-wrap gap-3 mb-3">
        <input type="search" value={q} onChange={(e) => setQ(e.target.value)} placeholder={t('admin.markets.search')} aria-label={t('admin.markets.search')} className="flex-1 min-w-[12rem] border border-gray-300 rounded px-3 py-1.5 text-sm" />
        <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={restrictedOnly} onChange={(e) => setRestrictedOnly(e.target.checked)} /> {t('admin.markets.restrictedOnly')}</label>
      </div>

      <section className="border border-gray-200 rounded-lg p-4 mb-4" aria-label={t('admin.markets.panel')}>
        <p className="text-sm font-medium mb-2">{t('admin.markets.selected', { n: selected.size })}</p>
        <p className="text-xs text-gray-500 mb-1">{t('admin.markets.pickCountries')}</p>
        <div className="flex flex-wrap gap-x-4 gap-y-1 text-sm mb-2">
          {known.map((c) => (
            <label key={c} className="flex items-center gap-1.5"><input type="checkbox" checked={countries.includes(c)} onChange={() => toggleCountry(c)} /> {c}</label>
          ))}
        </div>
        <input value={extra} onChange={(e) => setExtra(e.target.value)} placeholder={t('admin.markets.otherCountries')} aria-label={t('admin.markets.otherCountries')} className="w-full border border-gray-300 rounded px-3 py-1.5 text-sm mb-3" />
        <div className="flex flex-wrap gap-2">
          <button type="button" disabled={none || needCountries} onClick={() => apply('sold')} className="bg-brand text-white rounded px-3 py-1.5 text-sm disabled:opacity-40">{t('admin.markets.applySold')}</button>
          <button type="button" disabled={none || needCountries} onClick={() => apply('hidden')} className="border border-gray-300 rounded px-3 py-1.5 text-sm disabled:opacity-40">{t('admin.markets.applyHidden')}</button>
          <button type="button" disabled={none} onClick={() => apply('clear')} className="border border-gray-300 rounded px-3 py-1.5 text-sm disabled:opacity-40">{t('admin.markets.clear')}</button>
        </div>
        {error && <p role="alert" className="text-sm text-red-600 mt-2">{error}</p>}
        {msg && <p role="status" className="text-sm text-green-700 mt-2">{msg}</p>}
      </section>

      <div className="border border-gray-200 rounded-lg overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-left">
            <tr>
              <th scope="col" className="px-3 py-2 w-8"><input type="checkbox" checked={allOnPage} onChange={toggleAll} aria-label={t('admin.markets.selectPage')} /></th>
              <th scope="col" className="px-3 py-2">{t('admin.markets.product')}</th>
              <th scope="col" className="px-3 py-2">{t('admin.markets.soldIn')}</th>
              <th scope="col" className="px-3 py-2">{t('admin.markets.hiddenIn')}</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {rows.map((r) => (
              <tr key={r.id} className="hover:bg-gray-50">
                <td className="px-3 py-2"><input type="checkbox" checked={selected.has(r.id)} onChange={() => toggleRow(r.id)} aria-label={r.name} /></td>
                <td className="px-3 py-2"><span className="font-medium">{r.name}</span><span className="block text-xs text-gray-500">{r.category_name}</span></td>
                <td className="px-3 py-2">{r.sold_in_countries ? chips(r.sold_in_countries) : <span className="text-gray-500">{t('admin.markets.everywhere')}</span>}</td>
                <td className="px-3 py-2">{chips(r.hidden_in_countries)}</td>
              </tr>
            ))}
            {rows.length === 0 && <tr><td colSpan={4} className="px-3 py-6 text-center text-gray-500">{t('admin.markets.none')}</td></tr>}
          </tbody>
        </table>
      </div>
      <Pagination page={page} pageCount={Math.max(1, Math.ceil(total / PAGE_SIZE))} onChange={setPage} />
    </div>
  )
}
