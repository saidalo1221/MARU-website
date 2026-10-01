import { useEffect, useMemo, useRef, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { Link } from 'react-router-dom'
import { listCategories, listProducts } from '../api/products'
import { listPageSections } from '../api/pageSections'
import FaqItem from '../components/FaqItem'
import { useLocale } from '../context/LocaleContext'
import { useCart } from '../context/CartContext'
import ProductCard from '../components/product/ProductCard'
import { trackEvent } from '../lib/analytics'
import Breadcrumbs from '../components/Breadcrumbs'
import Seo from '../components/Seo'
import { ProductGridSkeleton } from '../components/Skeleton'
import useDialogFocus from '../lib/useDialogFocus'

const PAGE_SIZE = 12
const SORT_VALUES = ['default', 'price_asc', 'price_desc', 'newest', 'rating']

function minPrice(product) {
  const prices = product.variants.flatMap((v) => v.skus.map((s) => Number(s.retail_price)))
  return prices.length ? Math.min(...prices) : Infinity
}

function flattenCategories(nodes) {
  return nodes.flatMap((c) => [c, ...flattenCategories(c.children || [])])
}

// `category` (from the category page, PRD ТЗ№2 §10) pins the list to that category and its
// subcategories and adds the category's own heading, description, image and SEO text.
export default function Catalog({ category = null }) {
  const { locale, t } = useLocale()
  const { cart } = useCart()
  const currency = cart?.currency
  const [products, setProducts] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  // The header menus and home page link here with ?capacity=<ml> and ?sort=<value>.
  const [searchParams] = useSearchParams()
  const urlCapacity = searchParams.get('capacity') || ''
  const urlSort = searchParams.get('sort') || ''
  const urlCategory = searchParams.get('category') || ''
  const [volumeFilter, setVolumeFilter] = useState(urlCapacity)
  const [availabilityFilter, setAvailabilityFilter] = useState(false)
  const [categoryFilter, setCategoryFilter] = useState(urlCategory)
  const [colorFilter, setColorFilter] = useState('')
  const [priceMin, setPriceMin] = useState('')
  const [priceMax, setPriceMax] = useState('')
  const [categories, setCategories] = useState([])
  const [faq, setFaq] = useState([])
  const [page, setPage] = useState(1)
  const [sort, setSort] = useState(SORT_VALUES.includes(urlSort) ? urlSort : 'default')
  const [filtersOpen, setFiltersOpen] = useState(false)
  const listTracked = useRef(false)
  const filtersDialogRef = useRef(null)
  useDialogFocus(filtersDialogRef, filtersOpen)

  useEffect(() => {
    if (!filtersOpen) return
    const onKey = (e) => e.key === 'Escape' && setFiltersOpen(false)
    document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  }, [filtersOpen])

  useEffect(() => {
    setVolumeFilter(urlCapacity)
    setCategoryFilter(urlCategory)
    setSort(SORT_VALUES.includes(urlSort) ? urlSort : 'default')
  }, [urlCapacity, urlSort, urlCategory])

  const SORT_OPTIONS = [
    { value: 'default', label: t('catalog.sortDefault') },
    { value: 'price_asc', label: t('catalog.sortPriceAsc') },
    { value: 'price_desc', label: t('catalog.sortPriceDesc') },
    { value: 'newest', label: t('catalog.sortNewest') },
    { value: 'rating', label: t('catalog.sortRating') },
  ]

  useEffect(() => {
    listCategories(locale).then((tree) => setCategories(flattenCategories(tree))).catch(() => setCategories([]))
  }, [locale])

  useEffect(() => {
    setLoading(true)
    listProducts(locale, currency)
      .then((list) => {
        setProducts(list)
        // Refetches on currency/locale change must not count as new list views.
        if (!listTracked.current) {
          listTracked.current = true
          trackEvent('view_item_list', { item_list_name: 'catalog', item_count: list.length })
        }
      })
      .catch(setError)
      .finally(() => setLoading(false))
  }, [locale, currency])

  const volumes = useMemo(
    () => [...new Set(products.map((p) => p.volume_ml))].sort((a, b) => a - b),
    [products]
  )

  const colors = useMemo(
    () => [...new Set(products.flatMap((p) => p.variants.map((v) => v.color)))].sort(),
    [products]
  )
  // Product category ids the pinned category page covers (itself and its children).
  const pinnedIds = useMemo(
    () => (category ? new Set([String(category.id), ...(category.children || []).map((c) => String(c.id))]) : null),
    [category]
  )
  useEffect(() => {
    if (category) listPageSections('faq', locale).then((rows) => setFaq(rows.slice(0, 4))).catch(() => {})
  }, [category, locale])

  const categoryOptions = useMemo(() => {
    const used = new Set(products.map((p) => p.category_id))
    return categories.filter((c) => used.has(c.id))
  }, [categories, products])

  const filtered = useMemo(() => {
    let list = [...products]
    if (volumeFilter) list = list.filter((p) => String(p.volume_ml) === volumeFilter)
    if (pinnedIds) list = list.filter((p) => pinnedIds.has(String(p.category_id)))
    else if (categoryFilter) list = list.filter((p) => String(p.category_id) === categoryFilter)
    if (colorFilter) list = list.filter((p) => p.variants.some((v) => v.color === colorFilter))
    if (priceMin !== '') list = list.filter((p) => minPrice(p) >= Number(priceMin))
    if (priceMax !== '') list = list.filter((p) => minPrice(p) <= Number(priceMax))
    if (availabilityFilter) {
      list = list.filter((p) =>
        p.variants.some((v) => v.skus.some((s) => s.available_quantity > 0))
      )
    }
    if (sort === 'price_asc') list.sort((a, b) => minPrice(a) - minPrice(b))
    if (sort === 'price_desc') list.sort((a, b) => minPrice(b) - minPrice(a))
    if (sort === 'newest') list.sort((a, b) => b.id - a.id)
    if (sort === 'rating') list.sort((a, b) => (b.rating_average || 0) - (a.rating_average || 0))
    return list
  }, [products, volumeFilter, categoryFilter, colorFilter, priceMin, priceMax, availabilityFilter, sort])

  // Any filter or sort change starts again from the first page.
  useEffect(() => setPage(1), [volumeFilter, categoryFilter, colorFilter, priceMin, priceMax, availabilityFilter, sort])

  const pageCount = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE))
  const visible = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE)
  const hasFilters = volumeFilter || categoryFilter || colorFilter || priceMin !== '' || priceMax !== '' || availabilityFilter
  const clearFilters = () => {
    setVolumeFilter('')
    setCategoryFilter('')
    setColorFilter('')
    setPriceMin('')
    setPriceMax('')
    setAvailabilityFilter(false)
  }

  const FiltersPanel = (
    <div className="space-y-4">
      <div>
        <label className="block text-sm font-medium mb-1">{t('catalog.capacity')}</label>
        <select
          aria-label={t('catalog.capacity')}
          value={volumeFilter}
          onChange={(e) => setVolumeFilter(e.target.value)}
          className="w-full border border-gray-300 rounded px-2 py-1.5 text-sm"
        >
          <option value="">{t('catalog.all')}</option>
          {volumes.map((v) => (
            <option key={v} value={v}>{t('catalog.ml', { n: v })}</option>
          ))}
        </select>
      </div>
      {!category && categoryOptions.length > 1 && (
        <div>
          <label className="block text-sm font-medium mb-1" htmlFor="filter-category">{t('catalog.category')}</label>
          <select
            id="filter-category"
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            className="w-full border border-gray-300 rounded px-2 py-1.5 text-sm"
          >
            <option value="">{t('catalog.all')}</option>
            {categoryOptions.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
          </select>
        </div>
      )}
      {colors.length > 1 && (
        <div>
          <label className="block text-sm font-medium mb-1" htmlFor="filter-color">{t('catalog.color')}</label>
          <select
            id="filter-color"
            value={colorFilter}
            onChange={(e) => setColorFilter(e.target.value)}
            className="w-full border border-gray-300 rounded px-2 py-1.5 text-sm"
          >
            <option value="">{t('catalog.all')}</option>
            {colors.map((c) => <option key={c} value={c}>{c}</option>)}
          </select>
        </div>
      )}
      <fieldset>
        <legend className="block text-sm font-medium mb-1">{t('catalog.price')}</legend>
        <div className="flex gap-2">
          <input
            type="number" min="0" inputMode="decimal" value={priceMin} onChange={(e) => setPriceMin(e.target.value)}
            aria-label={t('catalog.priceMin')} placeholder={t('catalog.priceMin')}
            className="w-full border border-gray-300 rounded px-2 py-1.5 text-sm"
          />
          <input
            type="number" min="0" inputMode="decimal" value={priceMax} onChange={(e) => setPriceMax(e.target.value)}
            aria-label={t('catalog.priceMax')} placeholder={t('catalog.priceMax')}
            className="w-full border border-gray-300 rounded px-2 py-1.5 text-sm"
          />
        </div>
      </fieldset>
      <label className="flex items-center gap-2 text-sm">
        <input
          type="checkbox"
          checked={availabilityFilter}
          onChange={(e) => setAvailabilityFilter(e.target.checked)}
        />
        {t('catalog.inStockOnly')}
      </label>
      {hasFilters && (
        <button type="button" onClick={clearFilters} className="text-sm text-brand underline">{t('catalog.clearFilters')}</button>
      )}
    </div>
  )

  return (
    <div className="max-w-7xl mx-auto px-4 py-6">
      <Seo title={category ? category.name : t('catalog.title')} description={category?.description || undefined} image={category?.image_url || undefined} />
      <Breadcrumbs
        items={[
          { to: '/', label: t('header.home') },
          ...(category ? [{ to: '/shop', label: t('header.shop') }] : []),
          ...(category?.parent ? [{ to: `/shop/${category.parent.slug}`, label: category.parent.name }] : []),
        ]}
        current={category ? category.name : t('header.shop')}
        className="mb-2"
      />
      <h1 className="text-2xl font-bold mb-2">{category ? category.name : t('catalog.title')}</h1>
      {category && (category.description || category.image_url) && (
        <div className="flex flex-wrap items-start gap-4 mb-4">
          {category.image_url && <img src={category.image_url} alt="" className="h-28 w-28 rounded-lg object-cover bg-gray-100" />}
          {category.description && <p className="flex-1 min-w-[16rem] text-gray-600 whitespace-pre-wrap">{category.description}</p>}
        </div>
      )}
      {category?.children?.length > 0 && (
        <ul aria-label={t('catalog.subcategories')} className="flex flex-wrap gap-2 mb-4">
          {category.children.map((c) => (
            <li key={c.id}>
              <Link to={`/shop/${c.slug}`} className="inline-block border border-gray-300 rounded px-3 py-1 text-sm hover:bg-gray-50">{c.name}</Link>
            </li>
          ))}
        </ul>
      )}

      <div className="flex items-center justify-between mb-4 md:hidden">
        <button
          onClick={() => setFiltersOpen(true)}
          className="border border-gray-300 rounded px-3 py-1.5 text-sm"
        >
          {t('catalog.filters')}
        </button>
        <select
          aria-label={t('catalog.sortBy')}
          value={sort}
          onChange={(e) => setSort(e.target.value)}
          className="border border-gray-300 rounded px-2 py-1.5 text-sm"
        >
          {SORT_OPTIONS.map((o) => (
            <option key={o.value} value={o.value}>{o.label}</option>
          ))}
        </select>
      </div>

      <div className="md:grid md:grid-cols-[220px_1fr] md:gap-8">
        <aside className="hidden md:block">{FiltersPanel}</aside>

        {filtersOpen && (
          <div ref={filtersDialogRef} className="fixed inset-0 z-50 md:hidden" role="dialog" aria-modal="true" aria-label={t('catalog.filters')}>
            <div className="absolute inset-0 bg-black/40" onClick={() => setFiltersOpen(false)} />
            <div className="absolute inset-x-0 bottom-0 max-h-[85vh] overflow-y-auto rounded-t-2xl bg-white p-4 shadow-xl">
              <div className="mx-auto mb-3 h-1 w-10 rounded bg-gray-300" aria-hidden="true" />
              <div className="flex justify-between items-center mb-4">
                <h2 className="font-bold">{t('catalog.filters')}</h2>
                <button onClick={() => setFiltersOpen(false)} aria-label={t('common.close')}>✕</button>
              </div>
              {FiltersPanel}
              <button
                onClick={() => setFiltersOpen(false)}
                className="mt-6 w-full bg-brand text-white py-2 rounded"
              >
                {t('catalog.apply')}
              </button>
            </div>
          </div>
        )}

        <div>
          <div className="hidden md:flex justify-end mb-4">
            <select
              aria-label={t('catalog.sortBy')}
              value={sort}
              onChange={(e) => setSort(e.target.value)}
              className="border border-gray-300 rounded px-2 py-1.5 text-sm"
            >
              {SORT_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>{o.label}</option>
              ))}
            </select>
          </div>

          {loading && products.length === 0 && <ProductGridSkeleton />}
          {error && <p role="alert" className="text-red-600">{t('catalog.loadError')}</p>}
          {!loading && !error && filtered.length === 0 && (
            <div className="text-gray-500">
              <p>{t('catalog.noProducts')}</p>
              {hasFilters && (
                <button type="button" onClick={clearFilters} className="mt-2 text-brand underline">{t('catalog.clearFilters')}</button>
              )}
            </div>
          )}
          {!loading && !error && filtered.length > 0 && (
            <p className="text-sm text-gray-500 mb-3" role="status">{t('catalog.results', { n: filtered.length })}</p>
          )}

          <h2 className="sr-only">{t('catalog.title')}</h2>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
            {visible.map((p) => (
              <ProductCard key={p.id} product={p} />
            ))}
          </div>

          {pageCount > 1 && (
            <nav aria-label={t('catalog.pagination')} className="flex items-center justify-center gap-3 mt-6 text-sm">
              <button
                type="button" disabled={page <= 1} onClick={() => setPage((n) => n - 1)}
                className="border border-gray-300 rounded px-3 py-1.5 disabled:opacity-40"
              >
                {t('catalog.prev')}
              </button>
              <span>{t('catalog.pageOf', { page, total: pageCount })}</span>
              <button
                type="button" disabled={page >= pageCount} onClick={() => setPage((n) => n + 1)}
                className="border border-gray-300 rounded px-3 py-1.5 disabled:opacity-40"
              >
                {t('catalog.next')}
              </button>
            </nav>
          )}
        </div>
      </div>

      {category?.seo_content && (
        <section className="mt-10 max-w-3xl text-sm text-gray-600 whitespace-pre-wrap" aria-label={category.name}>
          {category.seo_content}
        </section>
      )}
      {category && faq.length > 0 && (
        <section className="mt-10 max-w-3xl" aria-labelledby="category-faq">
          <h2 id="category-faq" className="text-xl font-bold mb-3">{t('home.faqTitle')}</h2>
          {faq.map((q) => <FaqItem key={q.id} question={q.title} answer={q.body} />)}
        </section>
      )}
    </div>
  )
}
