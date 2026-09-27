import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useCart } from '../context/CartContext'
import QuantitySelector from '../components/product/QuantitySelector'
import { ApiError } from '../api/client'

export default function Cart() {
  const { cart, loading, updateItem, removeItem, refresh } = useCart()
  const navigate = useNavigate()
  const [promoInput, setPromoInput] = useState('')
  const [promoError, setPromoError] = useState(null)

  if (loading && !cart) return <p className="max-w-4xl mx-auto px-4 py-8">Loading...</p>

  if (!cart || cart.items.length === 0) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-12 text-center">
        <p className="text-lg mb-2">Your cart is empty</p>
        <p className="text-sm text-gray-500 mb-6">Browse our containers and add something to your cart.</p>
        <Link to="/shop" className="bg-brand text-white px-6 py-3 rounded font-medium">
          Continue Shopping
        </Link>
      </div>
    )
  }

  const applyPromo = async () => {
    setPromoError(null)
    try {
      await refresh({ promoCode: promoInput.trim() })
    } catch (err) {
      setPromoError(err instanceof ApiError ? err.detail || 'Invalid promo code' : 'Invalid promo code')
    }
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-6">
      <h1 className="text-2xl font-bold mb-4">Your Cart</h1>

      <div className="md:grid md:grid-cols-[1fr_320px] md:gap-8">
        <div className="divide-y divide-gray-200">
          {cart.items.map((item) => (
            <div key={item.id} className="py-4 flex items-center gap-4">
              <div className="flex-1">
                <p className="font-medium text-sm">{item.sku_code}</p>
                <p className="text-xs text-gray-500">
                  {cart.currency} {Number(item.unit_price).toFixed(2)} each
                </p>
              </div>
              <QuantitySelector
                value={item.quantity}
                onChange={(q) => updateItem(item.sku_id, q)}
              />
              <p className="w-20 text-right font-medium">
                {cart.currency} {Number(item.line_total).toFixed(2)}
              </p>
              <button
                onClick={() => removeItem(item.sku_id)}
                className="text-red-500 text-sm"
                aria-label="Remove item"
              >
                Remove
              </button>
            </div>
          ))}
        </div>

        <div className="mt-6 md:mt-0 border border-gray-200 rounded-lg p-4 h-fit">
          <div className="flex gap-2 mb-4">
            <input
              type="text"
              value={promoInput}
              onChange={(e) => setPromoInput(e.target.value)}
              placeholder="Promo code"
              className="flex-1 border border-gray-300 rounded px-2 py-1.5 text-sm"
            />
            <button onClick={applyPromo} className="border border-brand text-brand rounded px-3 text-sm">
              Apply
            </button>
          </div>
          {promoError && <p className="text-xs text-red-600 mb-2">{promoError}</p>}
          {cart.promo_code && (
            <p className="text-xs text-green-600 mb-2">Promo applied: {cart.promo_code}</p>
          )}

          <dl className="text-sm space-y-1">
            <div className="flex justify-between">
              <dt className="text-gray-500">Subtotal</dt>
              <dd>{cart.currency} {Number(cart.subtotal).toFixed(2)}</dd>
            </div>
            {Number(cart.discount) > 0 && (
              <div className="flex justify-between text-green-600">
                <dt>Discount</dt>
                <dd>-{cart.currency} {Number(cart.discount).toFixed(2)}</dd>
              </div>
            )}
            <div className="flex justify-between">
              <dt className="text-gray-500">Delivery</dt>
              <dd>{Number(cart.delivery) > 0 ? `${cart.currency} ${Number(cart.delivery).toFixed(2)}` : 'Calculated at checkout'}</dd>
            </div>
            <div className="flex justify-between font-semibold text-base border-t border-gray-200 pt-2 mt-2">
              <dt>Total</dt>
              <dd>{cart.currency} {Number(cart.total).toFixed(2)}</dd>
            </div>
          </dl>

          <button
            onClick={() => navigate('/checkout')}
            className="w-full bg-brand text-white rounded py-3 font-medium mt-4"
          >
            Proceed to Checkout
          </button>
        </div>
      </div>
    </div>
  )
}
