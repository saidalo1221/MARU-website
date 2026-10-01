import { useEffect, useMemo, useRef, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { getProduct, listProducts } from '../api/products'
import { listPageSections } from '../api/pageSections'
import { trackEvent } from '../lib/analytics'
import { addToWishlist, getWishlist, removeFromWishlist } from '../api/wishlist'
import { markWishlist } from '../lib/wishlistStore'
import { useLocale } from '../context/LocaleContext'
import { useCart } from '../context/CartContext'
import { useAuth } from '../context/AuthContext'
import VariantSelector from '../components/product/VariantSelector'
import QuantitySelector from '../components/product/QuantitySelector'
import Reviews from '../components/product/Reviews'
import ProductCard from '../components/product/ProductCard'
import ProductGallery from '../components/product/ProductGallery'
import { ProductDetailSkeleton } from '../components/Skeleton'
import ProductBadges from '../components/product/ProductBadges'
import Breadcrumbs from '../components/Breadcrumbs'
import FaqItem from '../components/FaqItem'
import Seo from '../components/Seo'
import DeliveryEstimate from '../components/product/DeliveryEstimate'
import StockAlertForm from '../components/product/StockAlertForm'

// The price of one unit at `quantity`: the highest matching quantity tier, but
// never above the SKU's own price (same rule as app/services/pricing.py).
function unitPriceAt(sku, quantity) {
  const base = Number(sku.retail_price)
  const tier = [...(sku.quantity_tiers || [])].reverse().find((t) => quantity >= t.min_quantity)
  return tier ? Math.min(Number(tier.price), base) : base
}

// "1–9", "10–49", "50+" rows for the quantity price table.
function tierRows(sku) {
  const tiers = sku.quantity_tiers || []
  if (tiers.length === 0) return []
  const base = Number(sku.retail_price)
  const starts = [1, ...tiers.map((t) => t.min_quantity)]
  return starts.map((from, i) => {
    const to = starts[i + 1] != null ? starts[i + 1] - 1 : null
    return { from, to, price: i === 0 ? base : Math.min(Number(tiers[i - 1].price), base) }
  })
}

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
  const [status, setStatus] = useState(null)
  const [related, setRelated] = useState([])
  const [faq, setFaq] = useState([])

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
    listProducts(locale, currency, { sort: 'popularity', limit: 5 })
      .then((list) => setRelated(list.filter((p) => p.slug !== slug).slice(0, 4)))
      .catch(() => {})
  }, [slug, locale, currency])

  useEffect(() => {
    listPageSections('faq', locale).then((rows) => setFaq(rows.slice(0, 4))).catch(() => {})
  }, [locale])

  const variant = useMemo(
    () => product?.variants.find((v) => v.id === variantId) ?? null,
    [product, variantId]
  )
  const sku = variant?.skus.find((s) => s.is_active) ?? null
  const coverImage = variant?.images?.[0]?.image_url || variant?.photo_url

  // The product refetches when the cart currency loads; count one view per
  // product, not one per fetch.
  const viewedProductId = useRef(null)
  const productId = product?.id
  useEffect(() => {
    if (!productId || viewedProductId.current === productId) return
    viewedProductId.current = productId
    trackEvent('view_item', { product_id: productId, slug })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [productId])

  const handleSelectVariant = (id) => {
    setVariantId(id)
    trackEvent('select_variant', { product_id: product.id, variant_id: id })
  }

  useEffect(() => {
    if (!user || !sku) return
    getWishlist().then((items) => setWishlisted(items.some((i) => i.sku_id === sku.id))).catch(() => {})
  }, [user, sku])

  const handleToggleWishlist = async () => {
    if (!sku) return
    if (wishlisted) {
      await removeFromWishlist(sku.id)
      markWishlist(sku.id, false)
      setWishlisted(false)
    } else {
      await addToWishlist(sku.id)
      markWishlist(sku.id, true)
      setWishlisted(true)
    }
  }

  if (error) return <p role="alert" className="max-w-3xl mx-auto px-4 py-8 text-red-600">{t('productDetail.notFound')}</p>
  if (!product) return <ProductDetailSkeleton />

  const inStock = sku ? sku.available_quantity > 0 : false
  const maxQty = sku ? sku.available_quantity : undefined
  const onSale = sku && sku.special_price != null && Number(sku.special_price) < Number(sku.retail_price)
  const discount = onSale ? Math.round((1 - Number(sku.special_price) / Number(sku.retail_price)) * 100) : 0
  const rows = sku ? tierRows(sku) : []
  const unitNow = sku ? unitPriceAt(sku, quantity) : null
  const tierActive = (row) => quantity >= row.from && (row.to == null || quantity <= row.to)

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
    description: product.meta_description || product.description || undefined,
    image: coverImage || undefined,
    aggregateRating: product.rating_count > 0
      ? { '@type': 'AggregateRating', ratingValue: product.rating_average, reviewCount: product.rating_count }
      : undefined,
    offers: sku
      ? {
          '@type': 'Offer',
          price: Number(onSale ? sku.special_price : sku.retail_price).toFixed(2),
          priceCurrency: sku.currency,
          availability: inStock ? 'https://schema.org/InStock' : 'https://schema.org/OutOfStock',
        }
      : undefined,
  }

  return (
    <div className="max-w-5xl mx-auto px-4 py-6">
      <Seo title={product.seo_title || product.name} description={product.meta_description || product.description} image={coverImage} type="product" jsonLd={jsonLd} />
      <Breadcrumbs
        items={[{ to: '/', label: t('header.home') }, { to: '/shop', label: t('header.shop') }]}
        current={product.name}
      />

      <div className="grid md:grid-cols-2 gap-8">
        <div>
          <ProductGallery variant={variant} alt={product.name} />
        </div>

        <div>
          <ProductBadges badges={product.badges} className="mb-2" />
          <h1 className="text-2xl font-bold">{product.name}</h1>
          {sku && <p className="text-xs text-gray-500 mt-1">SKU: {sku.sku_code}</p>}
          {product.rating_count > 0 && (
            <p className="text-sm mt-1">
              <a href="#reviews" className="text-yellow-600 underline">
                ★ {product.rating_average} · {t('productDetail.ratingCount', { n: product.rating_count })}
              </a>
            </p>
          )}

          <p className="text-2xl font-semibold mt-3">
            {sku ? `${sku.currency} ${Number(onSale ? sku.special_price : sku.retail_price).toFixed(2)}` : '—'}
            {onSale && (
              <>
                {' '}
                <s className="text-base font-normal text-gray-500">{Number(sku.retail_price).toFixed(2)}</s>{' '}
                <span className="text-sm font-medium text-red-600">−{discount}%</span>
              </>
            )}
          </p>
          <p className={`text-sm mt-1 ${inStock ? 'text-green-700' : 'text-red-600'}`}>
            {inStock ? t('productDetail.inStockCount', { n: sku.available_quantity }) : t('productDetail.outOfStock')}
          </p>
          {sku && !inStock && <StockAlertForm key={sku.id} skuId={sku.id} />}

          {rows.length > 0 && (
            <div className="mt-4">
              <p className="text-sm font-medium mb-1">{t('productDetail.tiersTitle')}</p>
              <table className="w-full max-w-xs text-sm border border-gray-200 rounded">
                <tbody>
                  {rows.map((row) => (
                    <tr key={row.from} className={tierActive(row) ? 'bg-brand-light font-medium' : ''}>
                      <th scope="row" className="text-left px-3 py-1 font-normal">
                        {row.to == null ? t('productDetail.tierFrom', { from: row.from }) : t('productDetail.tierRange', { from: row.from, to: row.to })}
                      </th>
                      <td className="px-3 py-1 text-right">{sku.currency} {row.price.toFixed(2)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <p className="text-xs text-gray-500 mt-1">
                {t('productDetail.yourPrice', { qty: quantity, price: `${sku.currency} ${unitNow.toFixed(2)}` })}
              </p>
            </div>
          )}

          {product.variants.length > 1 && (
            <div className="mt-4">
              <VariantSelector
                variants={product.variants}
                selectedVariantId={variantId}
                onSelect={handleSelectVariant}
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
                className={`border rounded px-4 py-3 font-medium text-xl leading-none ${wishlisted ? 'border-red-400 text-red-600' : 'border-gray-300 text-gray-500'}`}
              >
                {wishlisted ? '♥' : '♡'}
              </button>
            )}
          </div>

          {status && (
            <p role={status.type === 'success' ? 'status' : 'alert'} className={`text-sm mt-2 ${status.type === 'success' ? 'text-green-700' : 'text-red-600'}`}>
              {status.message}
            </p>
          )}

          <p className="mt-3 text-sm">
            <Link
              to={`/quote?product=${encodeURIComponent(product.name)}&quantity=${quantity}`}
              className="text-brand underline"
            >
              {t('productDetail.requestQuote')}
            </Link>
          </p>

          <div className="mt-6 border-t border-gray-200 pt-4">
            <p className="text-sm font-medium">{t('productDetail.delivery')}</p>
            <DeliveryEstimate />
          </div>

          {product.description && (
            <div className="mt-6 border-t border-gray-200 pt-4">
              <p className="text-sm font-medium mb-2">{t('productDetail.description')}</p>
              <p className="text-sm text-gray-700 whitespace-pre-line">{product.description}</p>
            </div>
          )}

          {sku?.bundle_items?.length > 0 && (
            <div className="mt-6 border-t border-gray-200 pt-4">
              <p className="text-sm font-medium mb-2">{t('productDetail.setContents')}</p>
              <ul className="text-sm text-gray-700 space-y-1">
                {sku.bundle_items.map((i) => (
                  <li key={i.sku_code}>{i.quantity} × {i.product_name}{i.variant_name && i.variant_name !== i.product_name ? ` — ${i.variant_name}` : ''}</li>
                ))}
              </ul>
            </div>
          )}

          {[['contentAdvantages', product.advantages, true], ['contentUsage', product.usage_scenarios, true], ['contentMaterial', product.material_info, false], ['contentInstructions', product.instructions, false]].map(([key, text, asList]) => {
            const lines = (text || '').split('\n').map((l) => l.trim()).filter(Boolean)
            if (!lines.length) return null
            return (
              <div key={key} className="mt-6 border-t border-gray-200 pt-4">
                <p className="text-sm font-medium mb-2">{t(`productDetail.${key}`)}</p>
                {asList ? (
                  <ul className="text-sm text-gray-700 list-disc pl-5 space-y-1">{lines.map((l, i) => <li key={i}>{l}</li>)}</ul>
                ) : (
                  <p className="text-sm text-gray-700 whitespace-pre-line">{lines.join('\n')}</p>
                )}
              </div>
            )
          })}

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

          <div id="reviews">
            <Reviews slug={slug} />
          </div>
        </div>
      </div>

      {faq.length > 0 && (
        <section className="mt-12" aria-labelledby="product-faq">
          <div className="flex items-end justify-between gap-4 mb-3">
            <h2 id="product-faq" className="text-xl font-bold">{t('home.faqTitle')}</h2>
            <Link to="/faq" className="text-sm text-brand underline">{t('home.allQuestions')}</Link>
          </div>
          <div className="max-w-3xl">
            {faq.map((s) => <FaqItem key={s.id} question={s.title} answer={s.body} />)}
          </div>
        </section>
      )}

      {related.length > 0 && (
        <section className="mt-12" aria-labelledby="related-products">
          <h2 id="related-products" className="text-xl font-bold mb-4">{t('productDetail.recommended')}</h2>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {related.map((p) => <ProductCard key={p.id} product={p} />)}
          </div>
        </section>
      )}
    </div>
  )
}
