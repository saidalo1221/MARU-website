import { useEffect, useMemo, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { getProduct } from '../api/products'
import { listShippingCountries } from '../api/shipping'
import { addToWishlist, getWishlist, removeFromWishlist } from '../api/wishlist'
import { useLocale } from '../context/LocaleContext'
import { useCart } from '../context/CartContext'
import { useAuth } from '../context/AuthContext'
import VariantSelector from '../components/product/VariantSelector'
import QuantitySelector from '../components/product/QuantitySelector'
import Reviews from '../components/product/Reviews'
import ProductGallery from '../components/product/ProductGallery'
import { ProductDetailSkeleton } from '../components/Skeleton'
import ProductBadges from '../components/product/ProductBadges'
import Seo from '../components/Seo'

export default function ProductDetail() {
  const { slug } = useParams()
  const { locale, t } = useLocale()
  const { cart, addItem } = useCart()
  const { user } = useAuth()
  const currency = cart?.currency
  const navigate = useNavigate()
  const [wishlisted, setWishlisted] = useState(false)

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
    getProduct(slug, locale, currency)
      .then((p) => {
        setProduct(p)
        setVariantId(p.variants[0]?.id ?? null)
        setQuantity(p.min_order_quantity || 1)
      })
      .catch(setError)
  }, [slug, locale, currency])

  useEffect(() => {
    listShippingCountries().then(setCountries).catch(() => {})
  }, [])

  const variant = useMemo(
    () => product?.variants.find((v) => v.id === variantId) ?? null,
    [product, variantId]
  )
  const sku = variant?.skus.find((s) => s.is_active) ?? null
  const coverImage = variant?.images?.[0]?.image_url || variant?.photo_url

  useEffect(() => {
    if (!user || !sku) return
    getWishlist().then((items) => setWishlisted(items.some((i) => i.sku_id === sku.id))).catch(() => {})
  }, [user, sku])

  const handleToggleWishlist = async () => {
    if (!sku) return
    if (wishlisted) {
      await removeFromWishlist(sku.id)
      setWishlisted(false)
    } else {
      await addToWishlist(sku.id)
      setWishlisted(true)
    }
  }

  if (error) return <p className="max-w-3xl mx-auto px-4 py-8 text-red-600">{t('productDetail.notFound')}</p>
  if (!product) return <ProductDetailSkeleton />

  const inStock = sku ? sku.available_quantity > 0 : false
  const maxQty = sku ? sku.available_quantity : undefined

  const handleAddToCart = async () => {
    if (!sku) return
    setStatus(null)
    try {
      await addItem(sku.id, quantity)
      setStatus({ type: 'success', message: t('productDetail.addedToCart') })
    } catch {
      setStatus({ type: 'error', message: t('productDetail.addToCartError') })
    }
  }

  const handleBuyNow = async () => {
    if (!sku) return
    try {
      await addItem(sku.id, quantity)
      navigate('/checkout')
    } catch {
      setStatus({ type: 'error', message: t('productDetail.addToCartError') })
    }
  }

  const jsonLd = {
    '@context': 'https://schema.org',
    '@type': 'Product',
    name: product.name,
    description: product.description || undefined,
    image: coverImage || undefined,
    offers: sku
      ? {
          '@type': 'Offer',
          price: Number(sku.retail_price).toFixed(2),
          priceCurrency: sku.currency,
          availability: inStock ? 'https://schema.org/InStock' : 'https://schema.org/OutOfStock',
        }
      : undefined,
  }

  return (
    <div className="max-w-5xl mx-auto px-4 py-6">
      <Seo title={product.name} description={product.description} image={coverImage} type="product" jsonLd={jsonLd} />
      <nav className="text-xs text-gray-500 mb-4">{t('productDetail.breadcrumb', { name: product.name })}</nav>

      <div className="grid md:grid-cols-2 gap-8">
        <div>
          <ProductGallery variant={variant} alt={product.name} />
        </div>

        <div>
          <ProductBadges badges={product.badges} className="mb-2" />
          <h1 className="text-2xl font-bold">{product.name}</h1>
          {sku && <p className="text-xs text-gray-500 mt-1">SKU: {sku.sku_code}</p>}

          <p className="text-2xl font-semibold mt-3">
            {sku ? `${sku.currency} ${Number(sku.retail_price).toFixed(2)}` : '—'}
          </p>
          <p className={`text-sm mt-1 ${inStock ? 'text-green-600' : 'text-red-500'}`}>
            {inStock ? t('productDetail.inStockCount', { n: sku.available_quantity }) : t('productDetail.outOfStock')}
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
            <p className="text-sm font-medium mb-2">{t('productDetail.quantity')}</p>
            <QuantitySelector
              value={quantity}
              min={product.min_order_quantity || 1}
              max={maxQty}
              onChange={setQuantity}
            />
            {product.min_order_quantity > 1 && (
              <p className="text-xs text-gray-500 mt-1">
                {t('productDetail.minOrder', { n: product.min_order_quantity })}
              </p>
            )}
          </div>

          <div className="flex gap-3 mt-6 sticky bottom-0 bg-white py-2 md:static">
            <button
              onClick={handleAddToCart}
              disabled={!inStock}
              className="flex-1 border border-brand text-brand rounded py-3 font-medium disabled:opacity-40"
            >
              {t('productDetail.addToCart')}
            </button>
            <button
              onClick={handleBuyNow}
              disabled={!inStock}
              className="flex-1 bg-brand text-white rounded py-3 font-medium disabled:opacity-40"
            >
              {t('productDetail.buyNow')}
            </button>
            {user && (
              <button
                onClick={handleToggleWishlist}
                aria-label={wishlisted ? t('wishlist.remove') : t('wishlist.add')}
                className={`border rounded px-4 py-3 font-medium text-xl leading-none ${wishlisted ? 'border-red-400 text-red-500' : 'border-gray-300 text-gray-500'}`}
              >
                {wishlisted ? '♥' : '♡'}
              </button>
            )}
          </div>

          {status && (
            <p className={`text-sm mt-2 ${status.type === 'success' ? 'text-green-600' : 'text-red-600'}`}>
              {status.message}
            </p>
          )}

          <div className="mt-6 border-t border-gray-200 pt-4">
            <p className="text-sm font-medium mb-2">{t('productDetail.delivery')}</p>
            <select
              aria-label={t('productDetail.selectCountry')}
              value={country}
              onChange={(e) => setCountry(e.target.value)}
              className="border border-gray-300 rounded px-2 py-1.5 text-sm w-full max-w-xs"
            >
              <option value="">{t('productDetail.selectCountry')}</option>
              {countries.map((c) => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>
            {country && (
              <p className="text-xs text-gray-500 mt-2">
                {t('productDetail.deliveryNote', { country })}
              </p>
            )}
          </div>

          {product.description && (
            <div className="mt-6 border-t border-gray-200 pt-4">
              <p className="text-sm font-medium mb-2">{t('productDetail.description')}</p>
              <p className="text-sm text-gray-700 whitespace-pre-line">{product.description}</p>
            </div>
          )}

          <dl className="mt-6 border-t border-gray-200 pt-4 text-sm grid grid-cols-2 gap-y-1">
            <dt className="text-gray-500">{t('productDetail.volume')}</dt>
            <dd>{t('catalog.ml', { n: product.volume_ml })}</dd>
            <dt className="text-gray-500">{t('productDetail.material')}</dt>
            <dd>{product.material}</dd>
            {product.shape && (
              <>
                <dt className="text-gray-500">{t('productDetail.shape')}</dt>
                <dd>{product.shape}</dd>
              </>
            )}
            {product.country_of_origin && (
              <>
                <dt className="text-gray-500">{t('productDetail.madeIn')}</dt>
                <dd>{product.country_of_origin}</dd>
              </>
            )}
          </dl>

          <Reviews slug={slug} />
        </div>
      </div>
    </div>
  )
}
