import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useCart } from '../context/CartContext'
import { checkout, confirmPayment, getPaymentMethods } from '../api/orders'
import { listShippingCountries, listShippingMethods } from '../api/shipping'
import { ApiError } from '../api/client'
import StripePaymentForm from '../components/checkout/StripePaymentForm'
import PayPalButton from '../components/checkout/PayPalButton'

const emptyForm = {
  order_type: 'individual',
  first_name: '',
  last_name: '',
  phone: '',
  email: '',
  country: '',
  city: '',
  address_line: '',
  postal_code: '',
  delivery_method: '',
  payment_method: '',
  company_name: '',
  company_reg_number: '',
  company_tax_number: '',
  company_address: '',
  contact_person: '',
}

export default function Checkout() {
  const { cart } = useCart()
  const navigate = useNavigate()

  const [form, setForm] = useState(emptyForm)
  const [countries, setCountries] = useState([])
  const [methods, setMethods] = useState([])
  const [paymentMethods, setPaymentMethods] = useState([])
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState(null)
  const [checkoutResult, setCheckoutResult] = useState(null)
  const [paymentError, setPaymentError] = useState(null)

  useEffect(() => {
    listShippingCountries().then(setCountries).catch(() => {})
    getPaymentMethods().then(setPaymentMethods).catch(() => {})
  }, [])

  useEffect(() => {
    if (!form.country) {
      setMethods([])
      return
    }
    listShippingMethods(form.country).then(setMethods).catch(() => setMethods([]))
  }, [form.country])

  const update = (field) => (e) => setForm((f) => ({ ...f, [field]: e.target.value }))

  if (!cart || cart.items.length === 0) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-12 text-center">
        <p>Your cart is empty.</p>
      </div>
    )
  }

  const enabledPaymentMethods = paymentMethods.filter((m) => m.enabled)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      const payload = { ...form }
      if (form.order_type !== 'legal_entity') {
        delete payload.company_name
        delete payload.company_reg_number
        delete payload.company_tax_number
        delete payload.company_address
        delete payload.contact_person
      }
      const result = await checkout(payload)
      if (result.guest_order_token) {
        sessionStorage.setItem(`maru_order_token_${result.id}`, result.guest_order_token)
      }
      setCheckoutResult(result)

      if (result.payment.reference_kind === 'redirect_url') {
        window.location.href = result.payment.reference
        return
      }
      // Stripe/PayPal need a client-side confirmation step, rendered below.
    } catch (err) {
      setError(err instanceof ApiError ? (err.detail || 'Checkout failed') : 'Checkout failed')
    } finally {
      setSubmitting(false)
    }
  }

  const handlePaymentSuccess = async () => {
    try {
      const orderToken = sessionStorage.getItem(`maru_order_token_${checkoutResult.id}`)
      await confirmPayment(checkoutResult.id, orderToken)
    } catch {
      // confirm-payment failure still leaves the order visible on the status page
    }
    navigate(`/orders/${checkoutResult.id}`)
  }

  if (checkoutResult && checkoutResult.payment.reference_kind !== 'redirect_url') {
    return (
      <div className="max-w-md mx-auto px-4 py-10">
        <h1 className="text-xl font-bold mb-4">Complete Payment</h1>
        <p className="text-sm text-gray-500 mb-4">
          Order {checkoutResult.order_number} — {checkoutResult.currency}{' '}
          {Number(checkoutResult.total_amount).toFixed(2)}
        </p>
        {paymentError && <p className="text-sm text-red-600 mb-3">{paymentError}</p>}
        {checkoutResult.payment.reference_kind === 'client_secret' && (
          <StripePaymentForm
            clientSecret={checkoutResult.payment.reference}
            onSuccess={handlePaymentSuccess}
            onError={setPaymentError}
          />
        )}
        {checkoutResult.payment.reference_kind === 'provider_order_id' && (
          <PayPalButton
            providerOrderId={checkoutResult.payment.reference}
            onApprove={handlePaymentSuccess}
            onError={setPaymentError}
          />
        )}
      </div>
    )
  }

  return (
    <div className="max-w-5xl mx-auto px-4 py-6">
      <h1 className="text-2xl font-bold mb-4">Checkout</h1>

      <div className="md:grid md:grid-cols-[1fr_320px] md:gap-8">
        <form onSubmit={handleSubmit} className="space-y-6">
          <fieldset>
            <legend className="font-semibold mb-2">Order type</legend>
            <div className="flex gap-4 text-sm">
              <label className="flex items-center gap-1">
                <input
                  type="radio"
                  checked={form.order_type === 'individual'}
                  onChange={() => setForm((f) => ({ ...f, order_type: 'individual' }))}
                />
                Individual
              </label>
              <label className="flex items-center gap-1">
                <input
                  type="radio"
                  checked={form.order_type === 'legal_entity'}
                  onChange={() => setForm((f) => ({ ...f, order_type: 'legal_entity' }))}
                />
                Company
              </label>
            </div>
          </fieldset>

          <fieldset className="grid grid-cols-2 gap-3">
            <legend className="font-semibold mb-2 col-span-2">Contact information</legend>
            <input required placeholder="First name" value={form.first_name} onChange={update('first_name')} className="border border-gray-300 rounded px-3 py-2 text-sm" />
            <input required placeholder="Last name" value={form.last_name} onChange={update('last_name')} className="border border-gray-300 rounded px-3 py-2 text-sm" />
            <input required type="tel" placeholder="Phone" value={form.phone} onChange={update('phone')} className="border border-gray-300 rounded px-3 py-2 text-sm" />
            <input required type="email" placeholder="Email" value={form.email} onChange={update('email')} className="border border-gray-300 rounded px-3 py-2 text-sm" />
          </fieldset>

          {form.order_type === 'legal_entity' && (
            <fieldset className="grid grid-cols-2 gap-3">
              <legend className="font-semibold mb-2 col-span-2">Company details</legend>
              <input required placeholder="Company name" value={form.company_name} onChange={update('company_name')} className="border border-gray-300 rounded px-3 py-2 text-sm col-span-2" />
              <input placeholder="Registration number" value={form.company_reg_number} onChange={update('company_reg_number')} className="border border-gray-300 rounded px-3 py-2 text-sm" />
              <input placeholder="Tax number" value={form.company_tax_number} onChange={update('company_tax_number')} className="border border-gray-300 rounded px-3 py-2 text-sm" />
              <input placeholder="Company address" value={form.company_address} onChange={update('company_address')} className="border border-gray-300 rounded px-3 py-2 text-sm col-span-2" />
              <input placeholder="Contact person" value={form.contact_person} onChange={update('contact_person')} className="border border-gray-300 rounded px-3 py-2 text-sm col-span-2" />
            </fieldset>
          )}

          <fieldset className="grid grid-cols-2 gap-3">
            <legend className="font-semibold mb-2 col-span-2">Shipping address</legend>
            <select required value={form.country} onChange={update('country')} className="border border-gray-300 rounded px-3 py-2 text-sm col-span-2">
              <option value="">Select country</option>
              {countries.map((c) => <option key={c} value={c}>{c}</option>)}
            </select>
            <input required placeholder="City" value={form.city} onChange={update('city')} className="border border-gray-300 rounded px-3 py-2 text-sm" />
            <input placeholder="Postal code" value={form.postal_code} onChange={update('postal_code')} className="border border-gray-300 rounded px-3 py-2 text-sm" />
            <input required placeholder="Address" value={form.address_line} onChange={update('address_line')} className="border border-gray-300 rounded px-3 py-2 text-sm col-span-2" />
          </fieldset>

          <fieldset>
            <legend className="font-semibold mb-2">Delivery method</legend>
            <select
              required
              value={form.delivery_method}
              onChange={update('delivery_method')}
              disabled={!form.country}
              className="border border-gray-300 rounded px-3 py-2 text-sm w-full"
            >
              <option value="">
                {form.country ? 'Select delivery method' : 'Select a country first'}
              </option>
              {methods.map((m) => <option key={m} value={m}>{m}</option>)}
            </select>
          </fieldset>

          <fieldset>
            <legend className="font-semibold mb-2">Payment method</legend>
            <div className="space-y-2">
              {enabledPaymentMethods.length === 0 && (
                <p className="text-sm text-gray-500">No payment methods are currently available.</p>
              )}
              {enabledPaymentMethods.map((m) => (
                <label key={m.id} className="flex items-center gap-2 text-sm">
                  <input
                    type="radio"
                    name="payment_method"
                    value={m.id}
                    checked={form.payment_method === m.id}
                    onChange={update('payment_method')}
                    required
                  />
                  {m.display_name}
                </label>
              ))}
            </div>
          </fieldset>

          {error && <p className="text-sm text-red-600">{error}</p>}

          <button
            type="submit"
            disabled={submitting}
            className="w-full bg-brand text-white rounded py-3 font-medium disabled:opacity-40 sticky bottom-0"
          >
            {submitting ? 'Placing order...' : 'Place Order'}
          </button>
        </form>

        <div className="mt-6 md:mt-0 border border-gray-200 rounded-lg p-4 h-fit">
          <h2 className="font-semibold mb-3">Order summary</h2>
          <ul className="text-sm space-y-1 mb-3">
            {cart.items.map((item) => (
              <li key={item.id} className="flex justify-between">
                <span>{item.sku_code} × {item.quantity}</span>
                <span>{cart.currency} {Number(item.line_total).toFixed(2)}</span>
              </li>
            ))}
          </ul>
          <dl className="text-sm space-y-1 border-t border-gray-200 pt-2">
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
              <dd>{Number(cart.delivery) > 0 ? `${cart.currency} ${Number(cart.delivery).toFixed(2)}` : 'TBD'}</dd>
            </div>
            <div className="flex justify-between font-semibold text-base border-t border-gray-200 pt-2 mt-2">
              <dt>Total</dt>
              <dd>{cart.currency} {Number(cart.total).toFixed(2)}</dd>
            </div>
          </dl>
        </div>
      </div>
    </div>
  )
}
