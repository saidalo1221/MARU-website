import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { adminCreateProduct, adminListCategories, adminListProducts, adminUpsertProductTranslation } from '../../api/admin'
import { errorMessage } from '../../api/client'
import { useLocale } from '../../context/LocaleContext'
import Money from '../../components/admin/Money'

const emptyForm = { category_id: '', name: '', slug: '', volume_ml: '', shape: '', purpose: '', description: '', country_of_origin: '', min_order_quantity: 1 }
const TRANSLATION_LOCALES = ['ru', 'uz', 'en']
const emptyTranslationFields = { name: '', description: '', shape: '', purpose: '', country_of_origin: '' }
const emptyTranslations = { ru: { ...emptyTranslationFields }, uz: { ...emptyTranslationFields }, en: { ...emptyTranslationFields } }

function flattenCategories(nodes, depth = 0) {
  return nodes.flatMap((n) => [{ ...n, depth }, ...flattenCategories(n.children || [], depth + 1)])
}

function cheapestSku(product) {
  const skus = product.variants.flatMap((v) => v.skus)
  return skus.reduce((min, s) => (!min || Number(s.retail_price) < Number(min.retail_price) ? s : min), null)
}

// A product only appears in the public shop once it has at least one active
// variant with an active SKU (app/routers/products.py's INNER JOIN) — a
// freshly created product has neither yet, so it stays invisible until an
// admin adds them on the detail page.
function isVisibleInShop(product) {
  return product.variants.some((v) => v.is_active && v.skus.some((s) => s.is_active))
}

// List + create here. Editing a product's own fields, plus its variants,
// SKUs, pricing, and per-warehouse inventory, happens on AdminProductDetail
// (/admin/products/:id).
export default function AdminProducts() {
  const { t } = useLocale()
  const navigate = useNavigate()
  const [products, setProducts] = useState([])
  const [categories, setCategories] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [form, setForm] = useState(emptyForm)
  const [translations, setTranslations] = useState(emptyTranslations)
  const [activeLocale, setActiveLocale] = useState('ru')
  const [formOpen, setFormOpen] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [formError, setFormError] = useState(null)

  const load = () => Promise.all([adminListProducts(), adminListCategories()])
    .then(([p, c]) => { setProducts(p); setCategories(flattenCategories(c)) })
    .catch((err) => setError(errorMessage(err, t('admin.products.loadFailed'))))
    .finally(() => setLoading(false))

  useEffect(() => { load() }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const update = (field) => (e) => setForm((f) => ({ ...f, [field]: e.target.value }))
  const updateTranslation = (field) => (e) =>
    setTranslations((t2) => ({ ...t2, [activeLocale]: { ...t2[activeLocale], [field]: e.target.value } }))

  const openNew = () => { setForm(emptyForm); setTranslations(emptyTranslations); setFormError(null); setFormOpen(true) }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setFormError(null)
    setSubmitting(true)
    try {
      const payload = { ...form, category_id: Number(form.category_id), volume_ml: Number(form.volume_ml), min_order_quantity: Number(form.min_order_quantity) }
      const created = await adminCreateProduct(payload)

      for (const locale of TRANSLATION_LOCALES) {
        const tr = translations[locale]
        if (tr.name.trim()) {
          await adminUpsertProductTranslation(created.id, locale, {
            name: tr.name,
            description: tr.description || null,
            shape: tr.shape || null,
            purpose: tr.purpose || null,
            country_of_origin: tr.country_of_origin || null,
          })
        }
      }

      setFormOpen(false)
      navigate(`/admin/products/${created.id}`)
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
      {error && <p role="alert" className="text-red-600 text-sm">{error}</p>}

      {formOpen && (
        <form onSubmit={handleSubmit} className="border border-gray-200 rounded-lg p-4 mb-6 grid grid-cols-2 gap-3">
          <select required value={form.category_id} aria-label={t('admin.products.selectCategory')} onChange={update('category_id')} className="border border-gray-300 rounded px-3 py-2 text-sm col-span-2">
            <option value="">{t('admin.products.selectCategory')}</option>
            {categories.map((c) => <option key={c.id} value={c.id}>{'  '.repeat(c.depth)}{c.name}</option>)}
          </select>
          <input required placeholder={t('admin.common.name')} aria-label={t('admin.common.name')} value={form.name} onChange={update('name')} className="border border-gray-300 rounded px-3 py-2 text-sm" />
          <input required placeholder={t('admin.common.slug')} aria-label={t('admin.common.slug')} value={form.slug} onChange={update('slug')} className="border border-gray-300 rounded px-3 py-2 text-sm" />
          <input required type="number" min="1" placeholder={t('admin.products.volumeMl')} aria-label={t('admin.products.volumeMl')} value={form.volume_ml} onChange={update('volume_ml')} className="border border-gray-300 rounded px-3 py-2 text-sm" />
          <input type="number" min="1" placeholder={t('admin.products.minOrderQty')} aria-label={t('admin.products.minOrderQty')} value={form.min_order_quantity} onChange={update('min_order_quantity')} className="border border-gray-300 rounded px-3 py-2 text-sm" />
          <input placeholder={t('admin.products.shape')} aria-label={t('admin.products.shape')} value={form.shape} onChange={update('shape')} className="border border-gray-300 rounded px-3 py-2 text-sm" />
          <input placeholder={t('admin.products.purpose')} aria-label={t('admin.products.purpose')} value={form.purpose} onChange={update('purpose')} className="border border-gray-300 rounded px-3 py-2 text-sm" />
          <input placeholder={t('admin.products.countryOfOrigin')} aria-label={t('admin.products.countryOfOrigin')} value={form.country_of_origin} onChange={update('country_of_origin')} className="border border-gray-300 rounded px-3 py-2 text-sm col-span-2" />
          <textarea placeholder={t('admin.products.description')} aria-label={t('admin.products.description')} value={form.description} onChange={update('description')} rows={3} className="border border-gray-300 rounded px-3 py-2 text-sm col-span-2" />

          <div className="col-span-2 border-t border-gray-100 pt-3">
            <p className="text-xs font-semibold text-gray-500 uppercase mb-2">{t('admin.blog.translations')}</p>
            <div className="flex gap-2 mb-2">
              {TRANSLATION_LOCALES.map((loc) => (
                <button
                  key={loc}
                  type="button"
                  onClick={() => setActiveLocale(loc)}
                  className={`px-2 py-1 rounded text-xs border ${activeLocale === loc ? 'bg-brand text-white border-brand' : 'border-gray-300'}`}
                >
                  {loc.toUpperCase()}
                </button>
              ))}
            </div>
            <div className="grid grid-cols-2 gap-2">
              <input placeholder={t('admin.common.name')} aria-label={t('admin.common.name')} value={translations[activeLocale].name} onChange={updateTranslation('name')} className="border border-gray-300 rounded px-3 py-2 text-sm" />
              <input placeholder={t('admin.products.description')} aria-label={t('admin.products.description')} value={translations[activeLocale].description} onChange={updateTranslation('description')} className="border border-gray-300 rounded px-3 py-2 text-sm" />
              <input placeholder={t('admin.products.shape')} aria-label={t('admin.products.shape')} value={translations[activeLocale].shape} onChange={updateTranslation('shape')} className="border border-gray-300 rounded px-3 py-2 text-sm" />
              <input placeholder={t('admin.products.purpose')} aria-label={t('admin.products.purpose')} value={translations[activeLocale].purpose} onChange={updateTranslation('purpose')} className="border border-gray-300 rounded px-3 py-2 text-sm" />
              <input placeholder={t('admin.products.countryOfOrigin')} aria-label={t('admin.products.countryOfOrigin')} value={translations[activeLocale].country_of_origin} onChange={updateTranslation('country_of_origin')} className="border border-gray-300 rounded px-3 py-2 text-sm" />
            </div>
          </div>

          {formError && <p role="alert" className="text-sm text-red-600 col-span-2">{formError}</p>}
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
                <th className="px-3 py-2">{t('admin.products.visibleInShop')}</th>
                <th className="px-3 py-2"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {products.map((p) => {
                const sku = cheapestSku(p)
                const visible = isVisibleInShop(p)
                return (
                  <tr key={p.id} className="hover:bg-gray-50">
                    <td className="px-3 py-2">{p.name}</td>
                    <td className="px-3 py-2 text-gray-500">{p.slug}</td>
                    <td className="px-3 py-2">{p.volume_ml} ml</td>
                    <td className="px-3 py-2">{sku ? <Money amount={sku.retail_price} currency={sku.currency} /> : '—'}</td>
                    <td className="px-3 py-2">{p.variants.length}</td>
                    <td className="px-3 py-2">
                      <span className={visible ? 'text-green-700' : 'text-amber-600'}>
                        {visible ? t('admin.common.yes') : t('admin.products.notVisibleYet')}
                      </span>
                    </td>
                    <td className="px-3 py-2 text-right"><Link to={`/admin/products/${p.id}`} className="text-brand">{t('admin.common.edit')}</Link></td>
                  </tr>
                )
              })}
              {products.length === 0 && <tr><td colSpan={7} className="px-3 py-6 text-center text-gray-400">{t('admin.products.none')}</td></tr>}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
