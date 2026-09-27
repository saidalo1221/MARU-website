import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { adminCreateProduct, adminListCategories, adminListProducts } from '../../api/admin'
import { errorMessage } from '../../api/client'
import { useLocale } from '../../context/LocaleContext'
import Money from '../../components/admin/Money'

const emptyForm = { category_id: '', name: '', slug: '', volume_ml: '', shape: '', purpose: '', description: '', country_of_origin: '', min_order_quantity: 1 }

function flattenCategories(nodes, depth = 0) {
  return nodes.flatMap((n) => [{ ...n, depth }, ...flattenCategories(n.children || [], depth + 1)])
}

function cheapestSku(product) {
  const skus = product.variants.flatMap((v) => v.skus)
  return skus.reduce((min, s) => (!min || Number(s.retail_price) < Number(min.retail_price) ? s : min), null)
}

// List + create here. Editing a product's own fields, plus its variants,
// SKUs, pricing, and per-warehouse inventory, happens on AdminProductDetail
// (/admin/products/:id).
export default function AdminProducts() {
  const { t } = useLocale()
  const [products, setProducts] = useState([])
  const [categories, setCategories] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [form, setForm] = useState(emptyForm)
  const [formOpen, setFormOpen] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [formError, setFormError] = useState(null)

  const load = () => Promise.all([adminListProducts(), adminListCategories()])
    .then(([p, c]) => { setProducts(p); setCategories(flattenCategories(c)) })
    .catch((err) => setError(errorMessage(err, t('admin.products.loadFailed'))))
    .finally(() => setLoading(false))

  useEffect(() => { load() }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const update = (field) => (e) => setForm((f) => ({ ...f, [field]: e.target.value }))

  const openNew = () => { setForm(emptyForm); setFormError(null); setFormOpen(true) }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setFormError(null)
    setSubmitting(true)
    try {
      const payload = { ...form, category_id: Number(form.category_id), volume_ml: Number(form.volume_ml), min_order_quantity: Number(form.min_order_quantity) }
      await adminCreateProduct(payload)
      setFormOpen(false)
      await load()
    } catch (err) {
      setFormError(errorMessage(err, t('admin.products.saveFailed')))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-2xl font-bold">{t('admin.products.title')}</h1>
        {!formOpen && <button onClick={openNew} className="bg-brand text-white px-4 py-2 rounded text-sm font-medium">{t('admin.products.add')}</button>}
      </div>

      {loading && <p>{t('admin.common.loading')}</p>}
      {error && <p className="text-red-600 text-sm">{error}</p>}

      {formOpen && (
        <form onSubmit={handleSubmit} className="border border-gray-200 rounded-lg p-4 mb-6 grid grid-cols-2 gap-3">
          <select required value={form.category_id} onChange={update('category_id')} className="border border-gray-300 rounded px-3 py-2 text-sm col-span-2">
            <option value="">{t('admin.products.selectCategory')}</option>
            {categories.map((c) => <option key={c.id} value={c.id}>{'  '.repeat(c.depth)}{c.name}</option>)}
          </select>
          <input required placeholder={t('admin.common.name')} value={form.name} onChange={update('name')} className="border border-gray-300 rounded px-3 py-2 text-sm" />
          <input required placeholder={t('admin.common.slug')} value={form.slug} onChange={update('slug')} className="border border-gray-300 rounded px-3 py-2 text-sm" />
          <input required type="number" min="1" placeholder={t('admin.products.volumeMl')} value={form.volume_ml} onChange={update('volume_ml')} className="border border-gray-300 rounded px-3 py-2 text-sm" />
          <input type="number" min="1" placeholder={t('admin.products.minOrderQty')} value={form.min_order_quantity} onChange={update('min_order_quantity')} className="border border-gray-300 rounded px-3 py-2 text-sm" />
          <input placeholder={t('admin.products.shape')} value={form.shape} onChange={update('shape')} className="border border-gray-300 rounded px-3 py-2 text-sm" />
          <input placeholder={t('admin.products.purpose')} value={form.purpose} onChange={update('purpose')} className="border border-gray-300 rounded px-3 py-2 text-sm" />
          <input placeholder={t('admin.products.countryOfOrigin')} value={form.country_of_origin} onChange={update('country_of_origin')} className="border border-gray-300 rounded px-3 py-2 text-sm col-span-2" />
          <textarea placeholder={t('admin.products.description')} value={form.description} onChange={update('description')} rows={3} className="border border-gray-300 rounded px-3 py-2 text-sm col-span-2" />
          {formError && <p className="text-sm text-red-600 col-span-2">{formError}</p>}
          <div className="col-span-2 flex gap-2">
            <button type="submit" disabled={submitting} className="bg-brand text-white px-4 py-2 rounded text-sm font-medium disabled:opacity-40">
              {submitting ? t('admin.common.saving') : t('admin.common.save')}
            </button>
            <button type="button" onClick={() => setFormOpen(false)} className="border border-gray-300 rounded px-4 py-2 text-sm">{t('admin.common.cancel')}</button>
          </div>
        </form>
      )}

      {!loading && !error && (
        <div className="border border-gray-200 rounded-lg overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-left">
              <tr>
                <th className="px-3 py-2">{t('admin.common.name')}</th>
                <th className="px-3 py-2">{t('admin.common.slug')}</th>
                <th className="px-3 py-2">{t('admin.products.volume')}</th>
                <th className="px-3 py-2">{t('admin.quoteDetail.price')}</th>
                <th className="px-3 py-2">{t('admin.products.variants')}</th>
                <th className="px-3 py-2"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {products.map((p) => {
                const sku = cheapestSku(p)
                return (
                  <tr key={p.id} className="hover:bg-gray-50">
                    <td className="px-3 py-2">{p.name}</td>
                    <td className="px-3 py-2 text-gray-500">{p.slug}</td>
                    <td className="px-3 py-2">{p.volume_ml} ml</td>
                    <td className="px-3 py-2">{sku ? <Money amount={sku.retail_price} currency={sku.currency} /> : '—'}</td>
                    <td className="px-3 py-2">{p.variants.length}</td>
                    <td className="px-3 py-2 text-right"><Link to={`/admin/products/${p.id}`} className="text-brand">{t('admin.common.edit')}</Link></td>
                  </tr>
                )
              })}
              {products.length === 0 && <tr><td colSpan={6} className="px-3 py-6 text-center text-gray-400">{t('admin.products.none')}</td></tr>}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
