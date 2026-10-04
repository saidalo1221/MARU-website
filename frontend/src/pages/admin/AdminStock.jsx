import { useEffect, useState } from 'react'
import { apiRequest, errorMessage, PAGE_SIZE } from '../../api/client'
import { useLocale } from '../../context/LocaleContext'
import Pagination from '../../components/ui/Pagination'
import { formatDateTime } from '../../lib/format'

export default function AdminStock() {
  const { t } = useLocale()
  const [warehouses, setWarehouses] = useState([])
  const [form, setForm] = useState({ sku_code: '', from: '', to: '', quantity: '', note: '' })
  const [rows, setRows] = useState([])
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const [error, setError] = useState(null)
  const [ok, setOk] = useState(false)

  const load = () =>
    apiRequest(`/admin/stock/movements${page > 1 ? `?page=${page}` : ''}`, { meta: true })
      .then(({ data, total: n }) => { setRows(data); setTotal(n) })
      .catch(() => setRows([]))

  useEffect(() => {
    apiRequest('/admin/warehouses/').then(setWarehouses).catch(() => {})
  }, [])
  useEffect(() => { load() }, [page]) // eslint-disable-line react-hooks/exhaustive-deps

  const name = (id) => warehouses.find((w) => w.id === id)?.name ?? (id ? `#${id}` : '—')

  const submit = async (e) => {
    e.preventDefault()
    setError(null)
    setOk(false)
    try {
      await apiRequest('/admin/stock/transfer', {
        method: 'POST',
        body: { sku_code: form.sku_code.trim(), from_warehouse_id: Number(form.from), to_warehouse_id: Number(form.to), quantity: Number(form.quantity), note: form.note.trim() || null },
      })
      setOk(true)
      setForm((f) => ({ ...f, quantity: '', note: '' }))
      setPage(1)
      await load()
    } catch (err) {
      setError(errorMessage(err, t('admin.stock.failed')))
    }
  }

  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }))
  const cls = 'border border-gray-300 rounded px-3 py-2 text-sm'

  return (
    <div>
      <h1 className="text-2xl font-bold mb-1">{t('admin.stock.title')}</h1>
      <p className="text-sm text-gray-500 mb-4">{t('admin.stock.subtitle')}</p>

      <form onSubmit={submit} className="border border-gray-200 rounded-lg p-4 mb-6 grid sm:grid-cols-2 gap-3">
        <input required placeholder={t('admin.stock.skuCode')} aria-label={t('admin.stock.skuCode')} value={form.sku_code} onChange={set('sku_code')} className={cls} />
        <input required type="number" min="1" placeholder={t('admin.stock.quantity')} aria-label={t('admin.stock.quantity')} value={form.quantity} onChange={set('quantity')} className={cls} />
        <select required aria-label={t('admin.stock.from')} value={form.from} onChange={set('from')} className={cls}>
          <option value="">{t('admin.stock.from')}</option>
          {warehouses.map((w) => <option key={w.id} value={w.id}>{w.name}</option>)}
        </select>
        <select required aria-label={t('admin.stock.to')} value={form.to} onChange={set('to')} className={cls}>
          <option value="">{t('admin.stock.to')}</option>
          {warehouses.map((w) => <option key={w.id} value={w.id}>{w.name}</option>)}
        </select>
        <input maxLength={300} placeholder={t('admin.stock.note')} aria-label={t('admin.stock.note')} value={form.note} onChange={set('note')} className={`${cls} sm:col-span-2`} />
        {error && <p role="alert" className="text-sm text-red-600 sm:col-span-2">{error}</p>}
        {ok && <p role="status" className="text-sm text-green-700 sm:col-span-2">{t('admin.stock.moved')}</p>}
        <button type="submit" className="bg-brand text-white rounded px-4 py-2 text-sm font-medium justify-self-start">{t('admin.stock.move')}</button>
      </form>

      <h2 className="font-semibold mb-2">{t('admin.stock.log')}</h2>
      <div className="border border-gray-200 rounded-lg overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-left">
            <tr>
              <th scope="col" className="px-3 py-2">{t('admin.stock.when')}</th>
              <th scope="col" className="px-3 py-2">{t('admin.stock.type')}</th>
              <th scope="col" className="px-3 py-2">{t('admin.stock.skuId')}</th>
              <th scope="col" className="px-3 py-2">{t('admin.stock.warehouse')}</th>
              <th scope="col" className="px-3 py-2">{t('admin.stock.quantity')}</th>
              <th scope="col" className="px-3 py-2">{t('admin.stock.note')}</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {rows.map((m) => (
              <tr key={m.id}>
                <td className="px-3 py-2 text-gray-500">{formatDateTime(m.created_at)}</td>
                <td className="px-3 py-2">{t(`admin.stock.type_${m.movement_type}`)}</td>
                <td className="px-3 py-2">{m.sku_id}</td>
                <td className="px-3 py-2">{m.movement_type === 'transfer' ? `${name(m.from_warehouse_id)} → ${name(m.to_warehouse_id)}` : name(m.to_warehouse_id)}</td>
                <td className="px-3 py-2">{m.quantity > 0 && m.movement_type === 'adjustment' ? `+${m.quantity}` : m.quantity}</td>
                <td className="px-3 py-2 text-gray-500">{m.note || '—'}</td>
              </tr>
            ))}
            {rows.length === 0 && <tr><td colSpan={6} className="px-3 py-6 text-center text-gray-500">{t('admin.stock.none')}</td></tr>}
          </tbody>
        </table>
      </div>
      <Pagination page={page} pageCount={Math.max(1, Math.ceil(total / PAGE_SIZE))} onChange={setPage} />
    </div>
  )
}
