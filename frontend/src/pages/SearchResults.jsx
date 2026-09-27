import { useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { listProducts } from '../api/products'
import { useLocale } from '../context/LocaleContext'
import { useCart } from '../context/CartContext'
import ProductCard from '../components/product/ProductCard'
import SearchBar from '../components/SearchBar'

// No server-side search endpoint exists yet; this filters the (currently
// small) active product list client-side. Replace with a real search
// endpoint once the catalog grows past a few hundred SKUs.
function matches(product, query) {
  const haystack = [
    product.name,
    product.slug,
    String(product.volume_ml),
    ...product.variants.flatMap((v) => [v.name, v.color, ...v.skus.map((s) => s.sku_code)]),
  ]
    .join(' ')
    .toLowerCase()
  return query
    .toLowerCase()
    .split(/\s+/)
    .filter(Boolean)
    .every((term) => haystack.includes(term))
}

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

  const results = useMemo(
    () => (query ? products.filter((p) => matches(p, query)) : products),
    [products, query]
  )

  return (
    <div className="max-w-7xl mx-auto px-4 py-6">
      <div className="mb-4 max-w-md">
        <SearchBar />
      </div>
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
