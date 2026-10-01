import { useEffect, useMemo, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { listCategories, listProducts } from '../api/products'
import { useLocale } from '../context/LocaleContext'
import { useCart } from '../context/CartContext'
import ProductCard from '../components/product/ProductCard'
import SearchBar from '../components/SearchBar'
import Seo from '../components/Seo'
import { trackEvent } from '../lib/analytics'
import { rankProducts } from '../lib/search'
import { ProductGridSkeleton } from '../components/Skeleton'

function minPrice(product) {
  const prices = product.variants.flatMap((v) => v.skus.map((s) => Number(s.retail_price)))
  return prices.length ? Math.min(...prices) : Infinity
}

function flattenCategories(nodes) {
  return nodes.flatMap((c) => [c, ...flattenCategories(c.children || [])])
}

// Search results (PRD ТЗ№2 §19): the query, the number of results, sorting and
// an availability filter, and - when nothing matches - ways forward.
export default function SearchResults() {
  const { locale, t } = useLocale()
  const { cart } = useCart()
  const currency = cart?.currency
  const [params] = useSearchParams()
  const query = params.get('q') || ''
  const [products, setProducts] = useState([])
  const [categories, setCategories] = useState([])
  const [loading, setLoading] = useState(true)
  const [sort, setSort] = useState('relevance')
  const [inStockOnly, setInStockOnly] = useState(false)

  useEffect(() => {
    setLoading(true)
    listProducts(locale, currency)
      .then(setProducts)
      .finally(() => setLoading(false))
  }, [locale, currency])

  useEffect(() => {
    listCategories(locale).then((tree) => setCategories(flattenCategories(tree))).catch(() => {})
  }, [locale])

  const ranked = useMemo(() => rankProducts(products, query), [products, query])
  const results = useMemo(() => {
    let list = [...ranked]
    if (inStockOnly) list = list.filter((p) => p.variants.some((v) => v.skus.some((s) => s.available_quantity > 0)))
    if (sort === 'price_asc') list.sort((a, b) => minPrice(a) - minPrice(b))
    if (sort === 'price_desc') list.sort((a, b) => minPrice(b) - minPrice(a))
    return list
  }, [ranked, inStockOnly, sort])
  // Best sellers first, then the rest, without repeating a product.
  const popular = useMemo(() => {
    const ordered = [...products.filter((p) => p.badges?.is_bestseller), ...products]
    return [...new Map(ordered.map((p) => [p.id, p])).values()].slice(0, 4)
  }, [products])

  useEffect(() => {
    if (!loading && query) trackEvent('search', { search_term: query.slice(0, 100), result_count: ranked.length })
    // Only when a search finishes loading for a new term, not on every re-rank.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [loading, query])

  const noMatches = !loading && ranked.length === 0

  return (
    <div className="max-w-7xl mx-auto px-4 py-6">
      <Seo title={query ? t('search_results.title', { query }) : t('search.button')} noindex />
      <div className="max-w-xl mb-4">
        <SearchBar />
      </div>
      <h1 className="text-sm font-normal text-gray-500 mb-4" role="status">
        {loading ? t('search_results.searching') : t('search_results.resultsFor', { count: results.length, query })}
      </h1>

      {!loading && ranked.length > 0 && (
        <div className="flex flex-wrap items-center gap-4 mb-4 text-sm">
          <label className="flex items-center gap-2">
            {t('catalog.sortBy')}
            <select value={sort} onChange={(e) => setSort(e.target.value)} className="border border-gray-300 rounded px-2 py-1.5 text-sm">
              <option value="relevance">{t('search_results.relevance')}</option>
              <option value="price_asc">{t('catalog.sortPriceAsc')}</option>
              <option value="price_desc">{t('catalog.sortPriceDesc')}</option>
            </select>
          </label>
          <label className="flex items-center gap-2">
            <input type="checkbox" checked={inStockOnly} onChange={(e) => setInStockOnly(e.target.checked)} />
            {t('catalog.inStockOnly')}
          </label>
        </div>
      )}

      {noMatches && (
        <div className="py-8 max-w-3xl">
          <p className="font-medium mb-1">{t('search_results.noneFound')}</p>
          <p className="text-sm text-gray-500 mb-6">{t('search_results.tryDifferent')}</p>

          {categories.length > 0 && (
            <div className="mb-6">
              <h2 className="font-semibold mb-2">{t('search_results.browseCategories')}</h2>
              <ul className="flex flex-wrap gap-2">
                {categories.map((c) => (
                  <li key={c.id}>
                    <Link to={`/shop?category=${c.id}`} className="inline-block border border-gray-300 rounded px-3 py-1 text-sm hover:bg-gray-50">{c.name}</Link>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {popular.length > 0 && (
            <div>
              <h2 className="font-semibold mb-3">{t('search_results.popular')}</h2>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                {popular.map((p) => <ProductCard key={p.id} product={p} />)}
              </div>
            </div>
          )}
        </div>
      )}

      {!loading && ranked.length > 0 && results.length === 0 && (
        <p className="text-gray-500 py-6">{t('catalog.noProducts')}</p>
      )}

      {loading && products.length === 0 && <ProductGridSkeleton />}

      {!noMatches && (
        <>
          <h2 className="sr-only">{t('catalog.title')}</h2>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
            {results.map((p) => (
              <ProductCard key={p.id} product={p} />
            ))}
          </div>
        </>
      )}
    </div>
  )
}
