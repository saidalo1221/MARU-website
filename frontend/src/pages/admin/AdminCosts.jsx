import { useEffect, useState } from 'react'
import { apiRequest, errorMessage, PAGE_SIZE } from '../../api/client'
import { useLocale } from '../../context/LocaleContext'
import Pagination from '../../components/ui/Pagination'

// What each SKU costs us, so the dashboard can show profit and margin. Edit one, or paste many.
export default function AdminCosts() {
  const { t } = useLocale()
  const [rows, setRows] = useState([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [q, setQ] = useState('')
  const [missingOnly, setMissingOnly] = useState(false)
  const [drafts, setDrafts] = useState({})
  const [error, setError] = useState(null)
  const [paste, setPaste] = useState('')
  const [report, setReport] = useState(null)

  const load = () => {
    const params = new URLSearchParams()
    if (q.trim()) params.set('q', q.trim())
    if (missingOnly) params.set('missing_only', 'true')
    if (page > 1) params.set('page', String(page))
    return apiRequest(`/admin/costs/${params.toString() ? `?${params}` : ''}`, { meta: true })
      .then(({ data, total: n }) => { setRows(data); setTotal(n); setDrafts({}) })
      .catch((err) => setError(errorMessage(err, t('admin.costs.failed'))))
  }

  useEffect(() => setPage(1), [q, missingOnly])
  useEffect(() => {
    const id = setTimeout(load, q ? 250 : 0)
    return () => clearTimeout(id)
  }, [q, missingOnly, page]) // eslint-disable-line react-hooks/exhaustive-deps

  const save = async (row) => {
    const raw = drafts[row.sku_id]
    if (raw === undefined) return
    setError(null)
    try {
      await apiRequest('/admin/costs/bulk', { method: 'PUT', body: { items: [{ sku_code: row.sku_code, cost_price: raw === '' ? null : Number(raw) }] } })
      await load()
    } catch (err) {
      setError(errorMessage(err, t('admin.costs.failed')))
    }
  }

  const importPaste = async () => {
    setError(null)
    setReport(null)
    const items = []
    for (const line of paste.split('\n').map((l) => l.trim()).filter(Boolean)) {
      const [code, value] = line.split(/[,;\t]/).map((x) => x.trim())
      if (!code || value === undefined || Number.isNaN(Number(value))) {
        setError(t('admin.costs.badLine', { line }))
        return
      }
      items.push({ sku_code: code, cost_price: value === '' ? null : Number(value) })
    }
    if (!items.length) return
    try {
      const r = await apiRequest('/admin/costs/bulk', { method: 'PUT', body: { items } })
      setReport(r)
      setPaste('')
      await load()
    } catch (err) {
      setError(errorMessage(err, t('admin.costs.failed')))
    }
  }

  return (
    <div>
      <h1 className="text-2xl font-bold mb-1">{t('admin.costs.title')}</h1>
      <p className="text-sm text-gray-500 mb-4">{t('admin.costs.subtitle')}</p>

      <div className="flex flex-wrap gap-3 mb-3">
        <input type="search" value={q} onChange={(e) => setQ(e.target.value)} placeholder={t('admin.costs.search')} aria-label={t('admin.costs.search')} className="flex-1 min-w-[12rem] border border-gray-300 rounded px-3 py-1.5 text-sm" />
        <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={missingOnly} onChange={(e) => setMissingOnly(e.target.checked)} /> {t('admin.costs.missingOnly')}</label>
      </div>
      {error && <p role="alert" className="text-sm text-red-600 mb-3">{error}</p>}

      <div className="border border-gray-200 rounded-lg overflow-x-auto mb-4">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-left">
            <tr>
              <th scope="col" className="px-3 py-2">{t('admin.costs.sku')}</th>
              <th scope="col" className="px-3 py-2">{t('admin.costs.price')}</th>
              <th scope="col" className="px-3 py-2">{t('admin.costs.cost')}</th>
              <th scope="col" className="px-3 py-2">{t('admin.costs.margin')}</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {rows.map((r) => (
              <tr key={r.sku_id}>
                <td className="px-3 py-2"><span className="font-medium">{r.sku_code}</span><span className="block text-xs text-gray-500">{r.product_name} · {r.variant_name}</span></td>
                <td className="px-3 py-2">{r.currency} {Number(r.retail_price).toFixed(2)}</td>
                <td className="px-3 py-2">
                  <div className="flex items-center gap-1">
                    <input type="number" min="0" step="0.01" aria-label={`${t('admin.costs.cost')}: ${r.sku_code}`} value={drafts[r.sku_id] ?? (r.cost_price ?? '')}
                      onChange={(e) => setDrafts((d) => ({ ...d, [r.sku_id]: e.target.value }))}
                      onBlur={() => save(r)} onKeyDown={(e) => e.key === 'Enter' && e.currentTarget.blur()}
                      className="w-28 border border-gray-300 rounded px-2 py-1 text-sm" />
                    <span className="text-xs text-gray-500">{r.currency}</span>
                  </div>
                </td>
                <td className="px-3 py-2">{r.margin_percent != null ? `${r.margin_percent}%` : <span className="text-gray-400">—</span>}</td>
              </tr>
            ))}
            {rows.length === 0 && <tr><td colSpan={4} className="px-3 py-6 text-center text-gray-500">{t('admin.costs.none')}</td></tr>}
          </tbody>
        </table>
      </div>
      <Pagination page={page} pageCount={Math.max(1, Math.ceil(total / PAGE_SIZE))} onChange={setPage} />

      <section className="border border-gray-200 rounded-lg p-4 mt-6" aria-labelledby="cost-import">
        <h2 id="cost-import" className="font-semibold mb-1">{t('admin.costs.importTitle')}</h2>
        <p className="text-xs text-gray-500 mb-2">{t('admin.costs.importHint')}</p>
        <textarea rows={5} value={paste} onChange={(e) => setPaste(e.target.value)} placeholder="SKU-350-TR, 4.20" aria-label={t('admin.costs.importTitle')} className="w-full border border-gray-300 rounded px-3 py-2 text-sm font-mono" />
        <button type="button" onClick={importPaste} disabled={!paste.trim()} className="border border-gray-300 rounded px-3 py-1.5 text-sm mt-2 disabled:opacity-40">{t('admin.costs.import')}</button>
        {report && (
          <p role="status" className="text-sm mt-2 text-green-700">
            {t('admin.costs.imported', { n: report.updated })}
            {report.unknown.length > 0 && <span className="text-red-600"> {t('admin.costs.unknown', { codes: report.unknown.slice(0, 10).join(', ') })}</span>}
          </p>
        )}
      </section>
    </div>
  )
}
