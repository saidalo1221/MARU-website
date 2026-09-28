import { useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { listProducts } from '../api/products'
import { useLocale } from '../context/LocaleContext'
import { useCart } from '../context/CartContext'
import ProductCard from '../components/product/ProductCard'
import { rankProducts } from '../lib/search'

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

  return (
    <div className="max-w-7xl mx-auto px-4 py-6">
      <p className="text-sm text-gray-500 mb-4">
        {loading ? t('search_results.searching') : t('search_results.resultsFor', { count: results.length, query })}
      </p>

      {!loading && results.length === 0 && (
        <div className="text-center py-12">
          <p className="mb-2">{t('search_results.noneFound')}</p>
          <p className="text-sm text-gray-500">{t('search_results.tryDifferent')}</p>
        </div>
      )}

      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
        {results.map((p) => (
          <ProductCard key={p.id} product={p} />
        ))}
      </div>
    </div>
  )
}
