import { useEffect, useMemo, useState } from 'react'
import { listProducts } from '../api/products'
import { useLocale } from '../context/LocaleContext'
import { useCart } from '../context/CartContext'
import ProductCard from '../components/product/ProductCard'
import { trackEvent } from '../lib/analytics'
import Seo from '../components/Seo'
import { ProductGridSkeleton } from '../components/Skeleton'

function minPrice(product) {
  const prices = product.variants.flatMap((v) => v.skus.map((s) => Number(s.retail_price)))
  return prices.length ? Math.min(...prices) : Infinity
}

export default function Catalog() {
  const { locale, t } = useLocale()
  const { cart } = useCart()
  const currency = cart?.currency
  const [products, setProducts] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [volumeFilter, setVolumeFilter] = useState('')
  const [availabilityFilter, setAvailabilityFilter] = useState(false)
  const [sort, setSort] = useState('default')
  const [filtersOpen, setFiltersOpen] = useState(false)

  useEffect(() => {
    if (!filtersOpen) return
    const onKey = (e) => e.key === 'Escape' && setFiltersOpen(false)
    document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  }, [filtersOpen])

  const SORT_OPTIONS = [
    { value: 'default', label: t('catalog.sortDefault') },
    { value: 'price_asc', label: t('catalog.sortPriceAsc') },
    { value: 'price_desc', label: t('catalog.sortPriceDesc') },
  ]

  useEffect(() => {
    setLoading(true)
    listProducts(locale, currency)
      .then((list) => {
        setProducts(list)
        trackEvent('view_item_list', { item_list_name: 'catalog', item_count: list.length })
      })
      .catch(setError)
      .finally(() => setLoading(false))
  }, [locale, currency])

  const volumes = useMemo(
    () => [...new Set(products.map((p) => p.volume_ml))].sort((a, b) => a - b),
    [products]
  )

  const visible = useMemo(() => {
    let list = [...products]
    if (volumeFilter) list = list.filter((p) => String(p.volume_ml) === volumeFilter)
    if (availabilityFilter) {
      list = list.filter((p) =>
        p.variants.some((v) => v.skus.some((s) => s.available_quantity > 0))
      )
    }
    if (sort === 'price_asc') list.sort((a, b) => minPrice(a) - minPrice(b))
    if (sort === 'price_desc') list.sort((a, b) => minPrice(b) - minPrice(a))
    return list
  }, [products, volumeFilter, availabilityFilter, sort])

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
      <label className="flex items-center gap-2 text-sm">
        <input
          type="checkbox"
          checked={availabilityFilter}
          onChange={(e) => setAvailabilityFilter(e.target.checked)}
        />
        {t('catalog.inStockOnly')}
      </label>
    </div>
  )

  return (
    <div className="max-w-7xl mx-auto px-4 py-6">
      <Seo title={t('catalog.title')} />
      <nav className="text-xs text-gray-500 mb-2">{t('catalog.breadcrumb')}</nav>
      <h1 className="text-2xl font-bold mb-4">{t('catalog.title')}</h1>

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
          <div className="fixed inset-0 z-50 md:hidden" role="dialog" aria-modal="true" aria-label={t('catalog.filters')}>
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
          {error && <p className="text-red-600">{t('catalog.loadError')}</p>}
          {!loading && !error && visible.length === 0 && (
            <p className="text-gray-500">{t('catalog.noProducts')}</p>
          )}

          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
            {visible.map((p) => (
              <ProductCard key={p.id} product={p} />
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
