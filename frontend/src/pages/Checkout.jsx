import { useEffect, useState } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { useCart } from '../context/CartContext'
import { useLocale } from '../context/LocaleContext'
import { checkout, confirmPayment, getPaymentMethods } from '../api/orders'
import { listAddresses } from '../api/addresses'
import { listShippingCountries, listShippingMethods } from '../api/shipping'
import { errorMessage } from '../api/client'
import StripePaymentForm from '../components/checkout/StripePaymentForm'
import PayPalButton from '../components/checkout/PayPalButton'
import MapPicker from '../components/MapPicker'
import Seo from '../components/Seo'

const NEW_ADDRESS = 'new'

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
  const { user, loading: authLoading } = useAuth()
  const { cart, refresh } = useCart()
  const { t } = useLocale()
  const navigate = useNavigate()

  const [form, setForm] = useState(emptyForm)
  const [pin, setPin] = useState(null)
  const [countries, setCountries] = useState([])
  const [methods, setMethods] = useState([])
  const [paymentMethods, setPaymentMethods] = useState([])
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState(null)
  const [checkoutResult, setCheckoutResult] = useState(null)
  const [paymentError, setPaymentError] = useState(null)

  const [savedAddresses, setSavedAddresses] = useState([])
  const [selectedAddressId, setSelectedAddressId] = useState(NEW_ADDRESS)

  useEffect(() => {
    listShippingCountries().then(setCountries).catch(() => {})
    getPaymentMethods().then(setPaymentMethods).catch(() => {})
  }, [])

  useEffect(() => {
    if (!user) return
    listAddresses()
      .then((addresses) => {
        setSavedAddresses(addresses)
        const preferred = addresses.find((a) => a.is_default) || addresses[0]
        if (preferred) selectAddress(preferred.id, addresses)
      })
      .catch(() => {})
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user])

  const selectAddress = (id, addresses = savedAddresses) => {
    if (id === NEW_ADDRESS) {
      setSelectedAddressId(NEW_ADDRESS)
      return
    }
    const address = addresses.find((a) => a.id === id)
    if (!address) return
    setSelectedAddressId(id)
    setPin(address.latitude != null && address.longitude != null ? { latitude: address.latitude, longitude: address.longitude } : null)
    setForm((f) => ({
      ...f,
      first_name: address.first_name,
      last_name: address.last_name,
      phone: address.phone,
      country: address.country,
      city: address.city,
      address_line: address.address_line,
      postal_code: address.postal_code,
    }))
  }

  useEffect(() => {
    if (!form.country) {
      setMethods([])
      return
    }
    listShippingMethods(form.country).then(setMethods).catch(() => setMethods([]))
  }, [form.country])

  // Re-fetch the cart's priced preview (tax/delivery/total) whenever the
  // buyer picks a country or delivery method, so the sidebar shows the real
  // computed amount instead of staying on the country-less "TBD" preview
  // from the initial page load.
  useEffect(() => {
    if (!form.country) return
    refresh({ country: form.country, deliveryMethod: form.delivery_method || undefined }).catch(() => {})
  }, [form.country, form.delivery_method, refresh])

  const update = (field) => (e) => setForm((f) => ({ ...f, [field]: e.target.value }))

  if (authLoading) return null
  if (!user) return <Navigate to="/login?next=/checkout" replace />

  if (!cart || cart.items.length === 0) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-12 text-center">
        <p>{t('checkout.empty')}</p>
      </div>
    )
  }

  const enabledPaymentMethods = paymentMethods.filter((m) => m.enabled)

  // Delivery methods come from the admin-configured ShippingRate table
  // (free-text, not an enum) — translate the known values, fall back to the
  // raw string for anything an admin names later.
  const methodLabel = (m) => {
    const key = `checkout.method.${m.toLowerCase()}`
    const resolved = t(key)
    return resolved === key ? m : resolved
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      const payload = { ...form, promo_code: cart.promo_code || null }
      if (form.order_type !== 'company') {
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
      setError(errorMessage(err, t('checkout.checkoutFailed')))
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
        <h1 className="text-xl font-bold mb-4">{t('checkout.completePayment')}</h1>
        <p className="text-sm text-gray-500 mb-4">
          {t('checkout.order', { number: checkoutResult.order_number })} — {checkoutResult.currency}{' '}
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
      <Seo title={t('checkout.title')} noindex />
      <h1 className="text-2xl font-bold mb-4">{t('checkout.title')}</h1>

      <div className="md:grid md:grid-cols-[1fr_320px] md:gap-8">
        <form onSubmit={handleSubmit} className="space-y-6">
          <fieldset>
            <legend className="font-semibold mb-2">{t('checkout.orderType')}</legend>
            <div className="flex gap-4 text-sm">
              <label className="flex items-center gap-1">
                <input
                  type="radio"
                  checked={form.order_type === 'individual'}
                  onChange={() => setForm((f) => ({ ...f, order_type: 'individual' }))}
                />
                {t('checkout.individual')}
              </label>
              <label className="flex items-center gap-1">
                <input
                  type="radio"
                  checked={form.order_type === 'company'}
                  onChange={() => setForm((f) => ({ ...f, order_type: 'company' }))}
                />
                {t('checkout.company')}
              </label>
            </div>
          </fieldset>

          <fieldset className="grid grid-cols-2 gap-3">
            <legend className="font-semibold mb-2 col-span-2">{t('checkout.contactInfo')}</legend>
            <input required placeholder={t('checkout.firstName')} value={form.first_name} onChange={update('first_name')} className="border border-gray-300 rounded px-3 py-2 text-sm" />
            <input required placeholder={t('checkout.lastName')} value={form.last_name} onChange={update('last_name')} className="border border-gray-300 rounded px-3 py-2 text-sm" />
            <input required type="tel" placeholder={t('checkout.phone')} value={form.phone} onChange={update('phone')} className="border border-gray-300 rounded px-3 py-2 text-sm" />
            <input required type="email" placeholder={t('checkout.email')} value={form.email} onChange={update('email')} className="border border-gray-300 rounded px-3 py-2 text-sm" />
          </fieldset>

          {form.order_type === 'company' && (
            <fieldset className="grid grid-cols-2 gap-3">
              <legend className="font-semibold mb-2 col-span-2">{t('checkout.companyDetails')}</legend>
              <input required placeholder={t('checkout.companyName')} value={form.company_name} onChange={update('company_name')} className="border border-gray-300 rounded px-3 py-2 text-sm col-span-2" />
              <input placeholder={t('checkout.regNumber')} value={form.company_reg_number} onChange={update('company_reg_number')} className="border border-gray-300 rounded px-3 py-2 text-sm" />
              <input placeholder={t('checkout.taxNumber')} value={form.company_tax_number} onChange={update('company_tax_number')} className="border border-gray-300 rounded px-3 py-2 text-sm" />
              <input placeholder={t('checkout.companyAddress')} value={form.company_address} onChange={update('company_address')} className="border border-gray-300 rounded px-3 py-2 text-sm col-span-2" />
              <input placeholder={t('checkout.contactPerson')} value={form.contact_person} onChange={update('contact_person')} className="border border-gray-300 rounded px-3 py-2 text-sm col-span-2" />
            </fieldset>
          )}

          <fieldset className="grid grid-cols-2 gap-3">
            <legend className="font-semibold mb-2 col-span-2">{t('checkout.shippingAddress')}</legend>

            {savedAddresses.length > 0 && (
              <div className="col-span-2 space-y-2 mb-2">
                {savedAddresses.map((a) => (
                  <label key={a.id} className="flex items-start gap-2 text-sm border border-gray-200 rounded px-3 py-2 cursor-pointer">
                    <input type="radio" name="saved_address" checked={selectedAddressId === a.id} onChange={() => selectAddress(a.id)} className="mt-1" />
                    <span>
                      {a.label && <span className="font-medium">{a.label} · </span>}
                      {a.first_name} {a.last_name} · {a.address_line}, {a.city}, {a.country} {a.postal_code}
                    </span>
                  </label>
                ))}
                <label className="flex items-center gap-2 text-sm border border-gray-200 rounded px-3 py-2 cursor-pointer">
                  <input type="radio" name="saved_address" checked={selectedAddressId === NEW_ADDRESS} onChange={() => selectAddress(NEW_ADDRESS)} />
                  {t('checkout.useNewAddress')}
                </label>
              </div>
            )}

            {selectedAddressId === NEW_ADDRESS && (
              <>
                <div className="col-span-2">
                  <MapPicker
                    latitude={pin?.latitude}
                    longitude={pin?.longitude}
                    onChange={setPin}
                    onReverseGeocode={({ country, city, addressLine, postalCode }) => {
                      const matchedCountry = countries.find((c) => c.toLowerCase() === country.toLowerCase())
                      setForm((f) => ({
                        ...f,
                        country: matchedCountry || f.country,
                        city: city || f.city,
                        address_line: addressLine || f.address_line,
                        postal_code: postalCode || f.postal_code,
                      }))
                    }}
                  />
                </div>
                <select required value={form.country} onChange={update('country')} className="border border-gray-300 rounded px-3 py-2 text-sm col-span-2">
                  <option value="">{t('checkout.selectCountry')}</option>
                  {countries.map((c) => <option key={c} value={c}>{c}</option>)}
                </select>
                <input required placeholder={t('checkout.city')} value={form.city} onChange={update('city')} className="border border-gray-300 rounded px-3 py-2 text-sm" />
                <input placeholder={t('checkout.postalCode')} value={form.postal_code} onChange={update('postal_code')} className="border border-gray-300 rounded px-3 py-2 text-sm" />
                <input required placeholder={t('checkout.address')} value={form.address_line} onChange={update('address_line')} className="border border-gray-300 rounded px-3 py-2 text-sm col-span-2" />
              </>
            )}
          </fieldset>

          <fieldset>
            <legend className="font-semibold mb-2">{t('checkout.deliveryMethod')}</legend>
            <select
              required
              value={form.delivery_method}
              onChange={update('delivery_method')}
              disabled={!form.country}
              className="border border-gray-300 rounded px-3 py-2 text-sm w-full"
            >
              <option value="">
                {form.country ? t('checkout.selectDeliveryMethod') : t('checkout.selectCountryFirst')}
              </option>
              {methods.map((m) => <option key={m} value={m}>{methodLabel(m)}</option>)}
            </select>
          </fieldset>

          <fieldset>
            <legend className="font-semibold mb-2">{t('checkout.paymentMethod')}</legend>
            <div className="space-y-2">
              {enabledPaymentMethods.length === 0 && (
                <p className="text-sm text-gray-500">{t('checkout.noPaymentMethods')}</p>
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
            {submitting ? t('checkout.placingOrder') : t('checkout.placeOrder')}
          </button>
        </form>

        <div className="mt-6 md:mt-0 border border-gray-200 rounded-lg p-4 h-fit">
          <h2 className="font-semibold mb-3">{t('checkout.orderSummary')}</h2>
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
              <dt className="text-gray-500">{t('cart.subtotal')}</dt>
              <dd>{cart.currency} {Number(cart.subtotal).toFixed(2)}</dd>
            </div>
            {Number(cart.discount) > 0 && (
              <div className="flex justify-between text-green-600">
                <dt>{t('cart.discount')}</dt>
                <dd>-{cart.currency} {Number(cart.discount).toFixed(2)}</dd>
              </div>
            )}
            <div className="flex justify-between">
              <dt className="text-gray-500">{t('productDetail.delivery')}</dt>
              <dd>{Number(cart.delivery) > 0 ? `${cart.currency} ${Number(cart.delivery).toFixed(2)}` : t('checkout.tbd')}</dd>
            </div>
            <div className="flex justify-between font-semibold text-base border-t border-gray-200 pt-2 mt-2">
              <dt>{t('cart.total')}</dt>
              <dd>{cart.currency} {Number(cart.total).toFixed(2)}</dd>
            </div>
          </dl>
        </div>
      </div>
    </div>
  )
}
