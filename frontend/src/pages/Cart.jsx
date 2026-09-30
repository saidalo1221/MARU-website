import { useEffect, useRef, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useCart } from '../context/CartContext'
import { useLocale } from '../context/LocaleContext'
import { getCartRecommendations } from '../api/cart'
import ProductCard from '../components/product/ProductCard'
import QuantitySelector from '../components/product/QuantitySelector'
import { errorMessage } from '../api/client'
import { trackEvent } from '../lib/analytics'
import Seo from '../components/Seo'

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
      <h2 id="saved-for-later-heading" className="font-semibold mb-2">
        {t('cart.savedTitle', { n: cart.saved_items.length })}
      </h2>
      {error && <p role="alert" className="text-sm text-red-600 mb-2">{error}</p>}
      <div className="divide-y divide-gray-200 border-t border-gray-200">
        {cart.saved_items.map((item) => (
          <div key={item.id} className="py-3 flex items-center gap-4 text-sm">
            <div className="flex-1">
              <p className="font-medium">{item.sku_code}</p>
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

  const cartItemCount = cart?.items.length ?? 0
  const cartViewTracked = useRef(false)
  useEffect(() => {
    if (cartItemCount > 0 && !cartViewTracked.current) {
      cartViewTracked.current = true
      trackEvent('view_cart', { item_count: cartItemCount, currency: cart.currency })
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [cartItemCount > 0])

  if (loading && !cart) return <p className="max-w-4xl mx-auto px-4 py-8">{t('cart.loading')}</p>

  if (!cart || cart.items.length === 0) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-12 text-center">
        <h1 className="text-lg mb-2">{t('cart.empty')}</h1>
        <p className="text-sm text-gray-500 mb-6">{t('cart.emptySubtitle')}</p>
        <Link to="/shop" className="bg-brand text-white px-6 py-3 rounded font-medium">
          {t('cart.continueShopping')}
        </Link>
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

  return (
    <div className="max-w-4xl mx-auto px-4 py-6">
      <Seo title={t('cart.title')} noindex />
      <h1 className="text-2xl font-bold mb-4">{t('cart.title')}</h1>

      <div className="md:grid md:grid-cols-[1fr_320px] md:gap-8">
        <div className="divide-y divide-gray-200">
          {cart.items.map((item) => (
            <div key={item.id} className="py-4 flex items-center gap-4">
              <div className="flex-1">
                <p className="font-medium text-sm">{item.sku_code}</p>
                <p className="text-xs text-gray-500">
                  {t('cart.each', { currency: cart.currency, price: Number(item.unit_price).toFixed(2) })}
                </p>
              </div>
              <QuantitySelector
                value={item.quantity}
                onChange={(q) => updateItem(item.sku_id, q)}
              />
              <p className="w-20 text-right font-medium">
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

        <div className="mt-6 md:mt-0 border border-gray-200 rounded-lg p-4 h-fit">
          <div className="flex gap-2 mb-4">
            <input
              type="text"
              value={promoInput}
              onChange={(e) => setPromoInput(e.target.value)}
              placeholder={t('cart.promoPlaceholder')}
              aria-label={t('cart.promoPlaceholder')}
              className="flex-1 border border-gray-300 rounded px-2 py-1.5 text-sm"
            />
            <button onClick={applyPromo} className="border border-brand text-brand rounded px-3 text-sm">
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
            <div className="flex justify-between font-semibold text-base border-t border-gray-200 pt-2 mt-2">
              <dt>{t('cart.total')}</dt>
              <dd>{cart.currency} {Number(cart.total).toFixed(2)}</dd>
            </div>
          </dl>

          <button
            onClick={() => navigate('/checkout')}
            className="w-full bg-brand text-white rounded py-3 font-medium mt-4"
          >
            {t('cart.checkoutButton')}
          </button>
        </div>
      </div>

      {recs && recs.products.length > 0 && (
        <section className="mt-10">
          <h2 className="text-lg font-semibold mb-3">
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
