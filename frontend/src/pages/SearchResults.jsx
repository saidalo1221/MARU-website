import { useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { listCategories, listProducts, queryProducts } from '../api/products'
import { useLocale } from '../context/LocaleContext'
import { useCart } from '../context/CartContext'
import ProductCard from '../components/product/ProductCard'
import Pagination from '../components/ui/Pagination'
import SearchBar from '../components/SearchBar'
import Seo from '../components/Seo'
import { trackEvent } from '../lib/analytics'
import { ProductGridSkeleton } from '../components/Skeleton'

const PAGE_SIZE = 12

function flattenCategories(nodes) {
  return nodes.flatMap((c) => [c, ...flattenCategories(c.children || [])])
}

// Search results (PRD ТЗ№2 §19): the query, the number of results, sorting and an availability filter,
// and - when nothing matches - ways forward. The server matches, ranks, filters and pages
// (name, SKU, category, size, typos), so this page never holds the whole catalogue.
export default function SearchResults() {
  const { locale, t } = useLocale()
  const { cart } = useCart()
  const currency = cart?.currency
  const [params] = useSearchParams()
  const query = params.get('q') || ''
  const [products, setProducts] = useState([])
  const [total, setTotal] = useState(0)
  const [categories, setCategories] = useState([])
  const [popular, setPopular] = useState([])
  const [loading, setLoading] = useState(true)
  const [sort, setSort] = useState('relevance')
  const [inStockOnly, setInStockOnly] = useState(false)
  const [page, setPage] = useState(1)

  useEffect(() => setPage(1), [query, sort, inStockOnly])

  useEffect(() => {
    if (!query.trim()) {
      setProducts([])
      setTotal(0)
      setLoading(false)
      return undefined
    }
    let current = true
    setLoading(true)
    queryProducts({
      lang: locale, currency, q: query, sort: sort === 'relevance' ? undefined : sort,
      availability: inStockOnly ? 'in_stock' : undefined, page, limit: PAGE_SIZE,
    })
      .then(({ data, total: n }) => {
        if (!current) return
        setProducts(data)
        setTotal(n)
        if (page === 1 && sort === 'relevance' && !inStockOnly) trackEvent('search', { search_term: query.slice(0, 100), result_count: n })
      })
      .catch(() => current && (setProducts([]), setTotal(0)))
      .finally(() => current && setLoading(false))
    return () => { current = false }
  }, [locale, currency, query, sort, inStockOnly, page])

  const noMatches = !loading && total === 0
  const unfiltered = !inStockOnly

  // "No results" help: categories to browse and a few popular products (only fetched when needed).
  useEffect(() => {
    if (!noMatches || !unfiltered) return
    listCategories(locale).then((tree) => setCategories(flattenCategories(tree))).catch(() => {})
    listProducts(locale, currency, { sort: 'popularity', limit: 4 }).then(setPopular).catch(() => {})
  }, [noMatches, unfiltered, locale, currency])

  return (
    <div className="max-w-7xl mx-auto px-4 py-6">
      <Seo title={query ? t('search_results.title', { query }) : t('search.button')} noindex />
      <div className="max-w-xl mb-4">
        <SearchBar />
      </div>
      <h1 className="text-sm font-normal text-gray-500 mb-4" role="status">
        {loading ? t('search_results.searching') : t('search_results.resultsFor', { count: total, query })}
      </h1>

      {(total > 0 || inStockOnly || sort !== 'relevance') && (
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

      {noMatches && unfiltered && (
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

      {noMatches && !unfiltered && <p className="text-gray-500 py-6">{t('catalog.noProducts')}</p>}

      {loading && products.length === 0 && <ProductGridSkeleton />}

      {total > 0 && (
        <>
          <h2 className="sr-only">{t('catalog.title')}</h2>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
            {products.map((p) => (
              <ProductCard key={p.id} product={p} />
            ))}
          </div>
          <Pagination page={page} pageCount={Math.max(1, Math.ceil(total / PAGE_SIZE))} onChange={setPage} />
        </>
      )}
    </div>
  )
}
