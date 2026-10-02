import { useEffect, useState } from 'react'
import { useLocale } from '../../context/LocaleContext'
import { listShippingCountries } from '../../api/shipping'
import { listProducts, suggestProducts } from '../../api/products'
import { createQuote } from '../../api/quotes'
import { errorMessage } from '../../api/client'

const emptyForm = {
  request_type: 'quote',
  name: '',
  company: '',
  country: '',
  city: '',
  email: '',
  phone: '',
  quantity: '',
  comment: '',
}

// Backs every "Request a Quote" / "Get Wholesale Price" / "Become a
// Distributor" / contact-form CTA on the site — there's only one inquiry
// endpoint on the backend (POST /quotes/, PRD section 32), so B2B/Wholesale/
// Distributor/Contact all submit through it with a different request_type.
// lockType hides the type selector for pages where it's implied by context
// (e.g. the Distributor page always submits request_type="distributor").
export default function InquiryForm({ defaultType = 'quote', lockType = false, ctaKey = 'quoteRequest.submit', initialProduct = null, initialQuantity = null }) {
  const { locale, t } = useLocale()
  const [form, setForm] = useState({ ...emptyForm, request_type: defaultType, quantity: initialQuantity || '' })
  const [countries, setCountries] = useState([])
  const [products, setProducts] = useState([])
  const [productQuery, setProductQuery] = useState('')
  const [selectedProducts, setSelectedProducts] = useState(initialProduct ? [initialProduct] : [])
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState(null)
  const [result, setResult] = useState(null)

  useEffect(() => {
    listShippingCountries().then(setCountries).catch(() => {})
  }, [])

  // Pick products by searching (the catalogue can be huge): the most popular ones show until you type.
  useEffect(() => {
    let current = true
    const q = productQuery.trim()
    const id = setTimeout(() => {
      const request = q
        ? suggestProducts(q, locale).then((r) => r.products)
        : listProducts(locale, undefined, { sort: 'popularity', limit: 8 })
      request.then((rows) => current && setProducts(rows)).catch(() => current && setProducts([]))
    }, q ? 250 : 0)
    return () => {
      current = false
      clearTimeout(id)
    }
  }, [locale, productQuery])

  const update = (field) => (e) => setForm((f) => ({ ...f, [field]: e.target.value }))

  const toggleProduct = (name) => {
    setSelectedProducts((prev) => (prev.includes(name) ? prev.filter((n) => n !== name) : [...prev, name]))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      const payload = {
        ...form,
        company: form.company || null,
        city: form.city || null,
        phone: form.phone || null,
        products: selectedProducts.length ? selectedProducts.join(', ') : null,
        quantity: form.quantity || null,
        comment: form.comment || null,
      }
      const quote = await createQuote(payload)
      setResult(quote)
    } catch (err) {
      setError(errorMessage(err, t('quoteRequest.submitFailed')))
    } finally {
      setSubmitting(false)
    }
  }

  if (result) {
    return (
      <div className="py-6 text-center">
        <h3 className="mb-2 text-xl font-semibold">{t('quoteRequest.thankYou')}</h3>
        <p className="text-sm text-gray-600">{t('quoteRequest.confirmation', { number: result.rfq_number })}</p>
      </div>
    )
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {!lockType && (
        <select aria-label={t('quoteRequest.requestType')} value={form.request_type} onChange={update('request_type')} className="w-full rounded-2xl border border-gray-300 bg-white px-4 py-2.5 text-sm">
          <option value="quote">{t('quoteRequest.typeQuote')}</option>
          <option value="wholesale">{t('quoteRequest.typeWholesale')}</option>
          <option value="distributor">{t('quoteRequest.typeDistributor')}</option>
        </select>
      )}
      <input required placeholder={t('quoteRequest.name')} aria-label={t('quoteRequest.name')} value={form.name} onChange={update('name')} className="w-full rounded-2xl border border-gray-300 bg-white px-4 py-2.5 text-sm" />
      <input placeholder={t('checkout.companyName')} aria-label={t('checkout.companyName')} value={form.company} onChange={update('company')} className="w-full rounded-2xl border border-gray-300 bg-white px-4 py-2.5 text-sm" />
      <div className="grid grid-cols-2 gap-3">
        <select required aria-label={t('checkout.selectCountry')} value={form.country} onChange={update('country')} className="rounded-2xl border border-gray-300 bg-white px-4 py-2.5 text-sm">
          <option value="">{t('checkout.selectCountry')}</option>
          {countries.map((c) => <option key={c} value={c}>{c}</option>)}
        </select>
        <input placeholder={t('checkout.city')} aria-label={t('checkout.city')} value={form.city} onChange={update('city')} className="rounded-2xl border border-gray-300 bg-white px-4 py-2.5 text-sm" />
      </div>
      <input required type="email" placeholder={t('checkout.email')} aria-label={t('checkout.email')} value={form.email} onChange={update('email')} className="w-full rounded-2xl border border-gray-300 bg-white px-4 py-2.5 text-sm" />
      <input type="tel" placeholder={t('checkout.phone')} aria-label={t('checkout.phone')} value={form.phone} onChange={update('phone')} className="w-full rounded-2xl border border-gray-300 bg-white px-4 py-2.5 text-sm" />
      <div>
        <p className="text-sm text-gray-600 mb-1">{t('quoteRequest.products')}</p>
        {selectedProducts.length > 0 && (
          <ul className="flex flex-wrap gap-2 mb-2">
            {selectedProducts.map((name) => (
              <li key={name} className="flex items-center gap-1 rounded-full bg-brand-light px-3 py-1 text-sm">
                {name}
                <button type="button" onClick={() => toggleProduct(name)} aria-label={`${t('quoteRequest.removeProduct')}: ${name}`} className="text-gray-500">×</button>
              </li>
            ))}
          </ul>
        )}
        <input type="search" value={productQuery} onChange={(e) => setProductQuery(e.target.value)} placeholder={t('quoteRequest.searchProducts')} aria-label={t('quoteRequest.searchProducts')} className="w-full rounded-2xl border border-gray-300 bg-white px-4 py-2.5 text-sm mb-1" />
        <div className="max-h-40 space-y-1 overflow-y-auto rounded-2xl border border-gray-300 bg-white px-4 py-3">
          {products.length === 0 && <p className="text-sm text-gray-500">{productQuery.trim() ? t('quoteRequest.noProductMatches') : t('quoteRequest.productsLoading')}</p>}
          {products.map((p) => (
            <label key={p.id} className="flex items-center gap-2 text-sm">
              <input type="checkbox" className="accent-brand" checked={selectedProducts.includes(p.name)} onChange={() => toggleProduct(p.name)} />
              {p.name}
            </label>
          ))}
        </div>
      </div>
      <input placeholder={t('quoteRequest.quantity')} aria-label={t('quoteRequest.quantity')} value={form.quantity} onChange={update('quantity')} className="w-full rounded-2xl border border-gray-300 bg-white px-4 py-2.5 text-sm" />
      <textarea placeholder={t('quoteRequest.comment')} aria-label={t('quoteRequest.comment')} value={form.comment} onChange={update('comment')} className="w-full rounded-2xl border border-gray-300 bg-white px-4 py-2.5 text-sm" rows={3} />
      {error && <p role="alert" className="text-sm text-red-600">{error}</p>}
      <button type="submit" disabled={submitting} className="w-full rounded-full bg-brand py-3 font-semibold text-white transition-colors hover:bg-brand-dark disabled:opacity-40">
        {submitting ? t('quoteRequest.submitting') : t(ctaKey)}
      </button>
    </form>
  )
}
