import { useEffect, useRef, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { getShippingEstimate } from '../api/shipping'
import { useShipCountry } from '../lib/shipCountry'
import { useCart } from '../context/CartContext'
import { useLocale } from '../context/LocaleContext'
import { getCartRecommendations } from '../api/cart'
import ProductCard from '../components/product/ProductCard'
import QuantitySelector from '../components/product/QuantitySelector'
import { errorMessage } from '../api/client'
import { trackEvent } from '../lib/analytics'
import Seo from '../components/Seo'

// "Estimated delivery: 2-5 days" for the country picked in the header (PRD ТЗ№2 §20).
function EstimatedDelivery() {
  const { t } = useLocale()
  const country = useShipCountry()
  const [estimate, setEstimate] = useState(null)
  useEffect(() => {
    getShippingEstimate(country).then(setEstimate).catch(() => setEstimate(null))
  }, [country])
  if (!estimate || estimate.max_days == null) return null
  const days = estimate.min_days != null && estimate.min_days !== estimate.max_days
    ? `${estimate.min_days}-${estimate.max_days}`
    : `${estimate.max_days}`
  return (
    <div className="flex justify-between">
      <dt className="text-gray-500">{t('cart.estimatedDelivery')}</dt>
      <dd>{t('orderStatus.estimatedDays', { days })}</dd>
    </div>
  )
}

function SavedForLater({ cart, removeItem, moveToCart }) {
  const { t } = useLocale()
  const [error, setError] = useState(null)
  if (!cart?.saved_items?.length) return null

  const move = async (skuId) => {
    setError(null)
    try {
      await moveToCart(skuId)
    } catch (err) {
      setError(errorMessage(err, t('cart.moveFailed')))
    }
  }

  return (
    <section className="mt-8" aria-labelledby="saved-for-later-heading">
      <h2 id="saved-for-later-heading" className="mb-3 text-lg font-semibold">
        {t('cart.savedTitle', { n: cart.saved_items.length })}
      </h2>
      {error && <p role="alert" className="text-sm text-red-600 mb-2">{error}</p>}
      <div className="space-y-2">
        {cart.saved_items.map((item) => (
          <div key={item.id} className="flex items-center gap-4 rounded-2xl border border-gray-200 bg-gray-50 px-4 py-3 text-sm">
            <div className="flex-1">
              <p className="font-medium">{item.product_name || item.sku_code}</p>
              <p className="text-xs text-gray-500">{[item.variant_name, item.sku_code].filter(Boolean).join(' · ')}</p>
              <p className="text-xs text-gray-500">
                {item.quantity} × {cart.currency} {Number(item.unit_price).toFixed(2)}
              </p>
            </div>
            <button onClick={() => move(item.sku_id)} className="text-brand">{t('cart.moveToCart')}</button>
            <button onClick={() => removeItem(item.sku_id)} className="text-red-600">{t('cart.remove')}</button>
          </div>
        ))}
      </div>
    </section>
  )
}

export default function Cart() {
  const { cart, loading, updateItem, removeItem, saveForLater, moveToCart, refresh } = useCart()
  const { t, locale } = useLocale()
  const navigate = useNavigate()
  const [promoInput, setPromoInput] = useState('')
  const [promoError, setPromoError] = useState(null)
  const [recs, setRecs] = useState(null)

  // Advisory only: refetch when the cart's contents or currency change, and
  // swallow any failure so a broken upsell can never get in the way of checkout.
  const cartKey = cart ? `${cart.currency}:${cart.items.map((i) => i.sku_id).join(',')}` : null
  useEffect(() => {
    if (!cartKey) return
    let cancelled = false
    getCartRecommendations({ lang: locale, currency: cart.currency })
      .then((data) => !cancelled && setRecs(data))
      .catch(() => !cancelled && setRecs(null))
    return () => {
      cancelled = true
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [cartKey, locale])

  // Names come from the server in the chosen language; reload them when it changes.
  const firstLocale = useRef(true)
  useEffect(() => {
    if (firstLocale.current) {
      firstLocale.current = false
      return
    }
    refresh().catch(() => {})
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [locale])

  const cartItemCount = cart?.items.length ?? 0
  const cartViewTracked = useRef(false)
  useEffect(() => {
    if (cartItemCount > 0 && !cartViewTracked.current) {
      cartViewTracked.current = true
      trackEvent('view_cart', { item_count: cartItemCount, currency: cart.currency })
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [cartItemCount > 0])

  if (loading && !cart) return <p className="mx-auto max-w-5xl px-4 py-10 text-gray-500">{t('cart.loading')}</p>

  if (!cart || cart.items.length === 0) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-12 md:py-16">
        <div className="rounded-3xl bg-brand-light px-6 py-14 text-center">
          <h1 className="mb-2 text-3xl font-semibold tracking-tight">{t('cart.empty')}</h1>
          <p className="mb-6 text-gray-600">{t('cart.emptySubtitle')}</p>
          <Link to="/shop" className="inline-block rounded-full bg-brand px-8 py-3 font-semibold text-white transition-colors hover:bg-brand-dark">
            {t('cart.continueShopping')}
          </Link>
        </div>
        <div className="text-left">
          <SavedForLater cart={cart} removeItem={removeItem} moveToCart={moveToCart} />
        </div>
      </div>
    )
  }

  const applyPromo = async () => {
    setPromoError(null)
    try {
      await refresh({ promoCode: promoInput.trim() })
    } catch (err) {
      setPromoError(errorMessage(err, t('cart.invalidPromo')))
    }
  }

  const belowMinimum = cart.items.some((i) => i.quantity < i.min_order_quantity)
  const unavailable = cart.unavailable_items > 0

  return (
    <div className="mx-auto max-w-5xl px-4 py-8 md:py-12">
      <Seo title={t('cart.title')} noindex />
      <h1 className="mb-6 text-3xl font-semibold tracking-tight md:text-4xl">{t('cart.title')}</h1>

      <div className="md:grid md:grid-cols-[minmax(0,1fr)_320px] md:gap-8">
        <div className="space-y-3">
          {cart.items.map((item) => (
            <div key={item.id} className="flex flex-wrap items-center gap-x-4 gap-y-3 rounded-3xl border border-gray-200 bg-gray-50 p-4 md:p-5">
              <Link to={item.product_slug ? `/products/${item.product_slug}` : '/shop'} className="shrink-0" tabIndex={-1} aria-hidden="true">
                {item.image_url ? (
                  <img src={item.image_url} alt="" loading="lazy" decoding="async" className="h-20 w-20 rounded-2xl bg-gray-100 object-cover" />
                ) : (
                  <span className="block h-20 w-20 rounded-2xl bg-gray-100" />
                )}
              </Link>
              <div className="flex-1 min-w-[9rem]">
                <p className="font-semibold">
                  {item.product_slug ? <Link to={`/products/${item.product_slug}`} className="hover:underline">{item.product_name || item.sku_code}</Link> : item.sku_code}
                </p>
                <p className="text-xs text-gray-500">
                  {[item.variant_name, item.sku_code].filter(Boolean).join(' · ')}
                </p>
                {item.available_in_market === false && <p className="text-xs text-red-600">{t('market.lineNotSold')}</p>}
                <p className="text-xs text-gray-500">
                  {t('cart.each', { currency: cart.currency, price: Number(item.unit_price).toFixed(2) })}
                  {item.list_price != null && (
                    <>
                      {' '}
                      <s>{Number(item.list_price).toFixed(2)}</s>{' '}
                      <span className="text-red-600">−{Math.round((1 - Number(item.unit_price) / Number(item.list_price)) * 100)}%</span>
                    </>
                  )}
                </p>
                {item.min_order_quantity > 1 && (
                  <p className={`text-xs mt-0.5 ${item.quantity < item.min_order_quantity ? 'text-red-600' : 'text-gray-500'}`}>
                    {t('cart.minOrder', { n: item.min_order_quantity })}
                  </p>
                )}
              </div>
              <QuantitySelector
                value={item.quantity}
                onChange={(q) => updateItem(item.sku_id, q)}
              />
              <p className="min-w-[7rem] whitespace-nowrap text-right text-lg font-semibold">
                {cart.currency} {Number(item.line_total).toFixed(2)}
              </p>
              <button onClick={() => saveForLater(item.sku_id)} className="text-brand text-sm">
                {t('cart.saveForLater')}
              </button>
              <button
                onClick={() => removeItem(item.sku_id)}
                className="text-red-600 text-sm"
                aria-label={t('cart.remove')}
              >
                {t('cart.remove')}
              </button>
            </div>
          ))}
          <SavedForLater cart={cart} removeItem={removeItem} moveToCart={moveToCart} />
        </div>

        <div className="mt-6 h-fit rounded-3xl border border-gray-200 bg-gray-50 p-6 md:sticky md:top-24 md:mt-0">
          <div className="flex gap-2 mb-4">
            <input
              type="text"
              value={promoInput}
              onChange={(e) => setPromoInput(e.target.value)}
              placeholder={t('cart.promoPlaceholder')}
              aria-label={t('cart.promoPlaceholder')}
              className="min-w-0 flex-1 rounded-full border border-gray-300 bg-white px-4 py-2 text-sm"
            />
            <button onClick={applyPromo} className="rounded-full border border-brand px-4 text-sm font-medium text-brand transition-colors hover:bg-brand-light">
              {t('catalog.apply')}
            </button>
          </div>
          {promoError && <p role="alert" className="text-xs text-red-600 mb-2">{promoError}</p>}
          {cart.promo_code && (
            <p className="text-xs text-green-700 mb-2">{t('cart.promoApplied', { code: cart.promo_code })}</p>
          )}

          {cart.free_shipping_threshold != null && (
            <p className="text-xs text-green-700 mb-2" role="status">
              {Number(cart.free_shipping_remaining) > 0
                ? t('cart.freeShippingRemaining', { amount: `${cart.currency} ${Number(cart.free_shipping_remaining).toFixed(2)}` })
                : t('cart.freeShippingUnlocked')}
            </p>
          )}

          <dl className="text-sm space-y-1">
            <div className="flex justify-between">
              <dt className="text-gray-500">{t('cart.subtotal')}</dt>
              <dd>{cart.currency} {Number(cart.subtotal).toFixed(2)}</dd>
            </div>
            {Number(cart.discount) > 0 && (
              <div className="flex justify-between text-green-700">
                <dt>{t('cart.discount')}</dt>
                <dd>-{cart.currency} {Number(cart.discount).toFixed(2)}</dd>
              </div>
            )}
            <div className="flex justify-between">
              <dt className="text-gray-500">{t('productDetail.delivery')}</dt>
              <dd>{Number(cart.delivery) > 0 ? `${cart.currency} ${Number(cart.delivery).toFixed(2)}` : t('cart.calculatedAtCheckout')}</dd>
            </div>
            <EstimatedDelivery />
            {cart.packaging && (cart.packaging.boxes > 0 || cart.packaging.loose_units > 0) && (
              <p className="text-xs text-gray-500">
                {t('cart.packLabel')}: {[
                  cart.packaging.boxes > 0 && t('cart.packBoxes', { n: cart.packaging.boxes }),
                  cart.packaging.loose_units > 0 && t('cart.packLoose', { n: cart.packaging.loose_units }),
                  cart.packaging.weight_kg > 0 && t('cart.packKg', { n: cart.packaging.weight_kg }),
                  cart.packaging.volume_l > 0 && t('cart.packLitres', { n: cart.packaging.volume_l }),
                ].filter(Boolean).join(' · ')}
                {cart.packaging.complete ? '' : t('cart.packagingApprox')}
              </p>
            )}
            <div className="mt-3 flex justify-between border-t border-gray-200 pt-3 text-xl font-semibold">
              <dt>{t('cart.total')}</dt>
              <dd>{cart.currency} {Number(cart.total).toFixed(2)}</dd>
            </div>
          </dl>

          {unavailable && <p role="alert" className="text-sm text-red-600 mt-3">{t('market.cartBlocked', { country: country })}</p>}
          <button
            onClick={() => navigate('/checkout')}
            disabled={belowMinimum || unavailable}
            className="mt-5 w-full rounded-full bg-brand py-3.5 font-semibold text-white transition-colors hover:bg-brand-dark active:scale-[0.98] disabled:opacity-40"
          >
            {t('cart.checkoutButton')}
          </button>
        </div>
      </div>

      {recs && recs.products.length > 0 && (
        <section className="mt-14">
          <h2 className="mb-5 text-2xl font-semibold tracking-tight">
            {recs.based_on_orders ? t('cart.boughtTogether') : t('cart.mayAlsoLike')}
          </h2>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            {recs.products.map((p) => (
              <ProductCard key={p.id} product={p} />
            ))}
          </div>
        </section>
      )}
    </div>
  )
}
