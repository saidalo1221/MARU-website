import { useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { listProducts } from '../api/products'
import { useLocale } from '../context/LocaleContext'
import { useCart } from '../context/CartContext'
import ProductCard from '../components/product/ProductCard'
import { trackEvent } from '../lib/analytics'
import { rankProducts } from '../lib/search'
import { ProductGridSkeleton } from '../components/Skeleton'

export default function SearchResults() {
  const { locale, t } = useLocale()
  const { cart } = useCart()
  const currency = cart?.currency
  const [params] = useSearchParams()
  const query = params.get('q') || ''
  const [products, setProducts] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    listProducts(locale, currency)
      .then(setProducts)
      .finally(() => setLoading(false))
  }, [locale, currency])

  const results = useMemo(() => rankProducts(products, query), [products, query])

  useEffect(() => {
    if (!loading && query) trackEvent('search', { search_term: query.slice(0, 100), result_count: results.length })
    // Only when a search finishes loading for a new term, not on every re-rank.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [loading, query])

  return (
    <div className="max-w-7xl mx-auto px-4 py-6">
      <h1 className="text-sm font-normal text-gray-500 mb-4">
        {loading ? t('search_results.searching') : t('search_results.resultsFor', { count: results.length, query })}
      </h1>

      {!loading && results.length === 0 && (
        <div className="text-center py-12">
          <p className="mb-2">{t('search_results.noneFound')}</p>
          <p className="text-sm text-gray-500">{t('search_results.tryDifferent')}</p>
        </div>
      )}

      {loading && products.length === 0 && <ProductGridSkeleton />}

      <h2 className="sr-only">{t('catalog.title')}</h2>
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
        {results.map((p) => (
          <ProductCard key={p.id} product={p} />
        ))}
      </div>
    </div>
  )
}
