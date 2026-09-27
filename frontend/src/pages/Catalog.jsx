import { useEffect, useMemo, useState } from 'react'
import { listProducts } from '../api/products'
import { useLocale } from '../context/LocaleContext'
import ProductCard from '../components/product/ProductCard'

const SORT_OPTIONS = [
  { value: 'default', label: 'Default' },
  { value: 'price_asc', label: 'Price: low to high' },
  { value: 'price_desc', label: 'Price: high to low' },
]

function minPrice(product) {
  const prices = product.variants.flatMap((v) => v.skus.map((s) => Number(s.retail_price)))
  return prices.length ? Math.min(...prices) : Infinity
}

export default function Catalog() {
  const { locale } = useLocale()
  const [products, setProducts] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [volumeFilter, setVolumeFilter] = useState('')
  const [availabilityFilter, setAvailabilityFilter] = useState(false)
  const [sort, setSort] = useState('default')
  const [filtersOpen, setFiltersOpen] = useState(false)

  useEffect(() => {
    setLoading(true)
    listProducts(locale)
      .then(setProducts)
      .catch(setError)
      .finally(() => setLoading(false))
  }, [locale])

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
        <label className="block text-sm font-medium mb-1">Capacity</label>
        <select
          value={volumeFilter}
          onChange={(e) => setVolumeFilter(e.target.value)}
          className="w-full border border-gray-300 rounded px-2 py-1.5 text-sm"
        >
          <option value="">All</option>
          {volumes.map((v) => (
            <option key={v} value={v}>{v} ml</option>
          ))}
        </select>
      </div>
      <label className="flex items-center gap-2 text-sm">
        <input
          type="checkbox"
          checked={availabilityFilter}
          onChange={(e) => setAvailabilityFilter(e.target.checked)}
        />
        In stock only
      </label>
    </div>
  )

  return (
    <div className="max-w-7xl mx-auto px-4 py-6">
      <nav className="text-xs text-gray-500 mb-2">Home / Shop</nav>
      <h1 className="text-2xl font-bold mb-4">All Containers</h1>

      <div className="flex items-center justify-between mb-4 md:hidden">
        <button
          onClick={() => setFiltersOpen(true)}
          className="border border-gray-300 rounded px-3 py-1.5 text-sm"
        >
          Filters
        </button>
        <select
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
          <div className="fixed inset-0 z-50 bg-white p-4 md:hidden overflow-y-auto">
            <div className="flex justify-between items-center mb-4">
              <h2 className="font-bold">Filters</h2>
              <button onClick={() => setFiltersOpen(false)} aria-label="Close filters">✕</button>
            </div>
            {FiltersPanel}
            <button
              onClick={() => setFiltersOpen(false)}
              className="mt-6 w-full bg-brand text-white py-2 rounded"
            >
              Apply
            </button>
          </div>
        )}

        <div>
          <div className="hidden md:flex justify-end mb-4">
            <select
              value={sort}
              onChange={(e) => setSort(e.target.value)}
              className="border border-gray-300 rounded px-2 py-1.5 text-sm"
            >
              {SORT_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>{o.label}</option>
              ))}
            </select>
          </div>

          {loading && <p>Loading...</p>}
          {error && <p className="text-red-600">Failed to load products.</p>}
          {!loading && !error && visible.length === 0 && (
            <p className="text-gray-500">No products found.</p>
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
