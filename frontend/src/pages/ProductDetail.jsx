import { useEffect, useMemo, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { getProduct } from '../api/products'
import { listShippingCountries } from '../api/shipping'
import { useLocale } from '../context/LocaleContext'
import { useCart } from '../context/CartContext'
import VariantSelector from '../components/product/VariantSelector'
import QuantitySelector from '../components/product/QuantitySelector'

export default function ProductDetail() {
  const { slug } = useParams()
  const { locale } = useLocale()
  const { addItem } = useCart()
  const navigate = useNavigate()

  const [product, setProduct] = useState(null)
  const [error, setError] = useState(null)
  const [variantId, setVariantId] = useState(null)
  const [quantity, setQuantity] = useState(1)
  const [countries, setCountries] = useState([])
  const [country, setCountry] = useState('')
  const [status, setStatus] = useState(null)

  useEffect(() => {
    setProduct(null)
    setError(null)
    getProduct(slug, locale)
      .then((p) => {
        setProduct(p)
        setVariantId(p.variants[0]?.id ?? null)
        setQuantity(p.min_order_quantity || 1)
      })
      .catch(setError)
  }, [slug, locale])

  useEffect(() => {
    listShippingCountries().then(setCountries).catch(() => {})
  }, [])

  const variant = useMemo(
    () => product?.variants.find((v) => v.id === variantId) ?? null,
    [product, variantId]
  )
  const sku = variant?.skus.find((s) => s.is_active) ?? null

  if (error) return <p className="max-w-3xl mx-auto px-4 py-8 text-red-600">Product not found.</p>
  if (!product) return <p className="max-w-3xl mx-auto px-4 py-8">Loading...</p>

  const inStock = sku ? sku.available_quantity > 0 : false
  const maxQty = sku ? sku.available_quantity : undefined

  const handleAddToCart = async () => {
    if (!sku) return
    setStatus(null)
    try {
      await addItem(sku.id, quantity)
      setStatus({ type: 'success', message: 'Added to cart' })
    } catch {
      setStatus({ type: 'error', message: 'Could not add to cart' })
    }
  }

  const handleBuyNow = async () => {
    if (!sku) return
    try {
      await addItem(sku.id, quantity)
      navigate('/checkout')
    } catch {
      setStatus({ type: 'error', message: 'Could not add to cart' })
    }
  }

  return (
    <div className="max-w-5xl mx-auto px-4 py-6">
      <nav className="text-xs text-gray-500 mb-4">Home / Shop / {product.name}</nav>

      <div className="grid md:grid-cols-2 gap-8">
        <div className="aspect-square bg-gray-100 rounded-lg overflow-hidden flex items-center justify-center">
          {variant?.photo_url ? (
            <img src={variant.photo_url} alt={product.name} className="w-full h-full object-cover" />
          ) : (
            <span className="text-gray-400">No image</span>
          )}
        </div>

        <div>
          <h1 className="text-2xl font-bold">{product.name}</h1>
          {sku && <p className="text-xs text-gray-500 mt-1">SKU: {sku.sku_code}</p>}

          <p className="text-2xl font-semibold mt-3">
            {sku ? `${sku.currency} ${Number(sku.retail_price).toFixed(2)}` : '—'}
          </p>
          <p className={`text-sm mt-1 ${inStock ? 'text-green-600' : 'text-red-500'}`}>
            {inStock ? `In stock (${sku.available_quantity} available)` : 'Out of stock'}
          </p>

          {product.variants.length > 1 && (
            <div className="mt-4">
              <VariantSelector
                variants={product.variants}
                selectedVariantId={variantId}
                onSelect={setVariantId}
              />
            </div>
          )}

          <div className="mt-4">
            <p className="text-sm font-medium mb-2">Quantity</p>
            <QuantitySelector
              value={quantity}
              min={product.min_order_quantity || 1}
              max={maxQty}
              onChange={setQuantity}
            />
            {product.min_order_quantity > 1 && (
              <p className="text-xs text-gray-500 mt-1">
                Minimum order quantity: {product.min_order_quantity}
              </p>
            )}
          </div>

          <div className="flex gap-3 mt-6 sticky bottom-0 bg-white py-2 md:static">
            <button
              onClick={handleAddToCart}
              disabled={!inStock}
              className="flex-1 border border-brand text-brand rounded py-3 font-medium disabled:opacity-40"
            >
              Add to Cart
            </button>
            <button
              onClick={handleBuyNow}
              disabled={!inStock}
              className="flex-1 bg-brand text-white rounded py-3 font-medium disabled:opacity-40"
            >
              Buy Now
            </button>
          </div>

          {status && (
            <p className={`text-sm mt-2 ${status.type === 'success' ? 'text-green-600' : 'text-red-600'}`}>
              {status.message}
            </p>
          )}

          <div className="mt-6 border-t border-gray-200 pt-4">
            <p className="text-sm font-medium mb-2">Delivery</p>
            <select
              value={country}
              onChange={(e) => setCountry(e.target.value)}
              className="border border-gray-300 rounded px-2 py-1.5 text-sm w-full max-w-xs"
            >
              <option value="">Select your country</option>
              {countries.map((c) => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>
            {country && (
              <p className="text-xs text-gray-500 mt-2">
                Exact delivery cost is calculated at checkout for {country}.
              </p>
            )}
          </div>

          {product.description && (
            <div className="mt-6 border-t border-gray-200 pt-4">
              <p className="text-sm font-medium mb-2">Description</p>
              <p className="text-sm text-gray-700 whitespace-pre-line">{product.description}</p>
            </div>
          )}

          <dl className="mt-6 border-t border-gray-200 pt-4 text-sm grid grid-cols-2 gap-y-1">
            <dt className="text-gray-500">Volume</dt>
            <dd>{product.volume_ml} ml</dd>
            <dt className="text-gray-500">Material</dt>
            <dd>{product.material}</dd>
            {product.shape && (
              <>
                <dt className="text-gray-500">Shape</dt>
                <dd>{product.shape}</dd>
              </>
            )}
            {product.country_of_origin && (
              <>
                <dt className="text-gray-500">Made in</dt>
                <dd>{product.country_of_origin}</dd>
              </>
            )}
          </dl>
        </div>
      </div>
    </div>
  )
}
