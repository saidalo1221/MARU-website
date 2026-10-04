import { useEffect, useMemo, useRef, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { Link } from 'react-router-dom'
import { getFacets, listCategories, queryProducts } from '../api/products'
import { listPageSections } from '../api/pageSections'
import FaqItem from '../components/FaqItem'
import { useLocale } from '../context/LocaleContext'
import { useShipCountry } from '../lib/shipCountry'
import { useCart } from '../context/CartContext'
import ProductCard from '../components/product/ProductCard'
import { trackEvent } from '../lib/analytics'
import Breadcrumbs from '../components/Breadcrumbs'
import Pagination from '../components/ui/Pagination'
import Seo from '../components/Seo'
import { ProductGridSkeleton } from '../components/Skeleton'
import useDialogFocus from '../lib/useDialogFocus'

const PAGE_SIZE = 12
const SORT_VALUES = ['default', 'price_asc', 'price_desc', 'newest', 'rating']

function flattenCategories(nodes) {
  return nodes.flatMap((c) => [c, ...flattenCategories(c.children || [])])
}

// `category` (from the category page, PRD ТЗ№2 §10) pins the list to that category and its
// subcategories and adds the category's own heading, description, image and SEO text.
export default function Catalog({ category = null }) {
  const { locale, t } = useLocale()
  const { cart } = useCart()
  const shipCountry = useShipCountry()
  const currency = cart?.currency
  const [products, setProducts] = useState([])
  const [total, setTotal] = useState(0)
  const [facets, setFacets] = useState({ capacities: [], colors: [], category_ids: [] })
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
  const [debouncedPrice, setDebouncedPrice] = useState({ min: '', max: '' })
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

  // Typing a price must not fire a request per keystroke.
  useEffect(() => {
    const id = setTimeout(() => setDebouncedPrice({ min: priceMin, max: priceMax }), 350)
    return () => clearTimeout(id)
  }, [priceMin, priceMax])

  // Product category ids the pinned category page covers (itself and its children).
  const pinnedList = useMemo(
    () => (category ? [category.id, ...(category.children || []).map((c) => c.id)].join(',') : ''),
    [category]
  )

  // Filter choices come from the server (it knows the whole catalogue; we only ever hold one page).
  useEffect(() => {
    getFacets(pinnedList).then(setFacets).catch(() => {})
  }, [pinnedList, shipCountry])

  // The server filters, sorts and pages; stale answers (the visitor kept clicking) are ignored.
  useEffect(() => {
    let current = true
    setLoading(true)
    setError(null)
    queryProducts({
      lang: locale,
      currency,
      categoryIds: pinnedList || categoryFilter,
      capacity: volumeFilter,
      color: colorFilter,
      availability: availabilityFilter ? 'in_stock' : undefined,
      priceMin: debouncedPrice.min,
      priceMax: debouncedPrice.max,
      sort,
      page,
      limit: PAGE_SIZE,
    })
      .then(({ data, total: n }) => {
        if (!current) return
        setProducts(data)
        setTotal(n)
        // Refetches on filter/page/currency change must not count as new list views.
        if (!listTracked.current) {
          listTracked.current = true
          trackEvent('view_item_list', { item_list_name: 'catalog', item_count: n })
        }
      })
      .catch((err) => current && setError(err))
      .finally(() => current && setLoading(false))
    return () => { current = false }
  }, [locale, currency, shipCountry, pinnedList, categoryFilter, volumeFilter, colorFilter, availabilityFilter, debouncedPrice, sort, page])

  const volumes = facets.capacities
  const colors = facets.colors
  useEffect(() => {
    if (category) listPageSections('faq', locale).then((rows) => setFaq(rows.slice(0, 4))).catch(() => {})
  }, [category, locale])

  const categoryOptions = useMemo(() => {
    const used = new Set(facets.category_ids)
    return categories.filter((c) => used.has(c.id))
  }, [categories, facets])

  // Any filter or sort change starts again from the first page.
  useEffect(() => setPage(1), [volumeFilter, categoryFilter, colorFilter, priceMin, priceMax, availabilityFilter, sort])

  const pageCount = Math.max(1, Math.ceil(total / PAGE_SIZE))
  const visible = products
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
    <div className="space-y-5">
      <div>
        <label className="block text-sm font-medium mb-1.5">{t('catalog.capacity')}</label>
        <select
          aria-label={t('catalog.capacity')}
          value={volumeFilter}
          onChange={(e) => setVolumeFilter(e.target.value)}
          className="w-full rounded-2xl border border-gray-300 bg-white px-3 py-2 text-sm"
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
            className="w-full rounded-2xl border border-gray-300 bg-white px-3 py-2 text-sm"
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
            className="w-full rounded-2xl border border-gray-300 bg-white px-3 py-2 text-sm"
          >
            <option value="">{t('catalog.all')}</option>
            {colors.map((c) => <option key={c} value={c}>{c}</option>)}
          </select>
        </div>
      )}
      <fieldset>
        <legend className="block text-sm font-medium mb-1.5">{t('catalog.price')}</legend>
        <div className="flex gap-2">
          <input
            type="number" min="0" inputMode="decimal" value={priceMin} onChange={(e) => setPriceMin(e.target.value)}
            aria-label={t('catalog.priceMin')} placeholder={t('catalog.priceMin')}
            className="w-full rounded-2xl border border-gray-300 bg-white px-3 py-2 text-sm"
          />
          <input
            type="number" min="0" inputMode="decimal" value={priceMax} onChange={(e) => setPriceMax(e.target.value)}
            aria-label={t('catalog.priceMax')} placeholder={t('catalog.priceMax')}
            className="w-full rounded-2xl border border-gray-300 bg-white px-3 py-2 text-sm"
          />
        </div>
      </fieldset>
      <label className="flex items-center gap-2 text-sm">
        <input
          type="checkbox"
          className="h-4 w-4 accent-brand"
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

  const sortSelect = (
    <select
      aria-label={t('catalog.sortBy')}
      value={sort}
      onChange={(e) => setSort(e.target.value)}
      className="rounded-full border border-gray-300 bg-white px-4 py-2 text-sm"
    >
      {SORT_OPTIONS.map((o) => (
        <option key={o.value} value={o.value}>{o.label}</option>
      ))}
    </select>
  )

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
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
      <h1 className="mb-6 text-3xl font-semibold tracking-tight md:text-4xl">{category ? category.name : t('catalog.title')}</h1>
      {category && (category.description || category.image_url) && (
        <div className="flex flex-wrap items-start gap-4 mb-4">
          {category.image_url && <img src={category.image_url} alt="" className="h-28 w-28 rounded-3xl object-cover bg-gray-100" />}
          {category.description && <p className="flex-1 min-w-[16rem] text-gray-600 whitespace-pre-wrap">{category.description}</p>}
        </div>
      )}
      {category?.children?.length > 0 && (
        <ul aria-label={t('catalog.subcategories')} className="flex flex-wrap gap-2 mb-4">
          {category.children.map((c) => (
            <li key={c.id}>
              <Link to={`/shop/${c.slug}`} className="inline-block rounded-full border border-gray-300 px-4 py-1.5 text-sm transition-colors hover:bg-brand-light">{c.name}</Link>
            </li>
          ))}
        </ul>
      )}

      <div className="mb-4 flex items-center justify-between gap-3 md:hidden">
        <button
          onClick={() => setFiltersOpen(true)}
          className="rounded-full border border-gray-300 bg-white px-5 py-2 text-sm font-medium"
        >
          {t('catalog.filters')}
        </button>
        {sortSelect}
      </div>

      <div className="md:grid md:grid-cols-[250px_1fr] md:gap-8">
        <aside className="hidden self-start rounded-3xl border border-gray-200 bg-gray-50 p-5 md:sticky md:top-24 md:block">{FiltersPanel}</aside>

        {filtersOpen && (
          <div ref={filtersDialogRef} className="fixed inset-0 z-50 md:hidden" role="dialog" aria-modal="true" aria-label={t('catalog.filters')}>
            <div className="absolute inset-0 bg-black/40" onClick={() => setFiltersOpen(false)} />
            <div className="absolute inset-x-0 bottom-0 max-h-[85vh] overflow-y-auto rounded-t-3xl bg-white p-5 shadow-xl">
              <div className="mx-auto mb-3 h-1 w-10 rounded bg-gray-300" aria-hidden="true" />
              <div className="flex justify-between items-center mb-4">
                <h2 className="font-bold">{t('catalog.filters')}</h2>
                <button onClick={() => setFiltersOpen(false)} aria-label={t('common.close')}>✕</button>
              </div>
              {FiltersPanel}
              <button
                onClick={() => setFiltersOpen(false)}
                className="mt-6 w-full rounded-full bg-brand py-3 font-semibold text-white"
              >
                {t('catalog.apply')}
              </button>
            </div>
          </div>
        )}

        <div>
          <div className="mb-4 hidden items-center justify-between md:flex">
            <p className="text-sm text-gray-500" role="status">
              {!loading && !error && total > 0 ? t('catalog.results', { n: total }) : ''}
            </p>
            {sortSelect}
          </div>

          {loading && products.length === 0 && <ProductGridSkeleton />}
          {error && <p role="alert" className="text-red-600">{t('catalog.loadError')}</p>}
          {!loading && !error && total === 0 && (
            <div className="rounded-3xl bg-brand-light px-6 py-14 text-center">
              <p className="text-lg text-gray-700">{t('catalog.noProducts')}</p>
              {hasFilters && (
                <button type="button" onClick={clearFilters} className="mt-5 rounded-full bg-brand px-6 py-2.5 text-sm font-semibold text-white hover:bg-brand-dark">{t('catalog.clearFilters')}</button>
              )}
            </div>
          )}
          {!loading && !error && total > 0 && (
            <p className="mb-3 text-sm text-gray-500 md:hidden" role="status">{t('catalog.results', { n: total })}</p>
          )}

          <h2 className="sr-only">{t('catalog.title')}</h2>
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 xl:grid-cols-4 md:gap-5">
            {visible.map((p) => (
              <ProductCard key={p.id} product={p} />
            ))}
          </div>

          <Pagination page={page} pageCount={pageCount} onChange={setPage} />
        </div>
      </div>

      {category?.seo_content && (
        <section className="mt-10 max-w-3xl text-sm text-gray-600 whitespace-pre-wrap" aria-label={category.name}>
          {category.seo_content}
        </section>
      )}
      {category && faq.length > 0 && (
        <section className="mt-10 max-w-3xl" aria-labelledby="category-faq">
          <h2 id="category-faq" className="mb-4 text-2xl font-semibold tracking-tight">{t('home.faqTitle')}</h2>
          {faq.map((q) => <FaqItem key={q.id} question={q.title} answer={q.body} />)}
        </section>
      )}
    </div>
  )
}
