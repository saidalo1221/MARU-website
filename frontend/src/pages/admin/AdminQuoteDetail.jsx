import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { adminConvertQuote, adminGetQuote, adminUpdateQuote } from '../../api/admin'
import { errorMessage } from '../../api/client'

const STATUSES = ['new', 'in_review', 'offered', 'accepted', 'rejected', 'expired']

export default function AdminQuoteDetail() {
  const { quoteId } = useParams()
  const navigate = useNavigate()
  const [quote, setQuote] = useState(null)
  const [error, setError] = useState(null)
  const [form, setForm] = useState({ status: '', proposed_price: '', currency: '', valid_until: '', manager_notes: '' })
  const [submitting, setSubmitting] = useState(false)

  const [convertForm, setConvertForm] = useState({ address_line: '', postal_code: '', delivery_method: '*', payment_method: 'invoice' })
  const [convertError, setConvertError] = useState(null)
  const [convertSubmitting, setConvertSubmitting] = useState(false)

  const load = () => adminGetQuote(quoteId).then((q) => {
    setQuote(q)
    setForm({
      status: q.status,
      proposed_price: q.proposed_price ?? '',
      currency: q.currency ?? '',
      valid_until: q.valid_until ? q.valid_until.slice(0, 10) : '',
      manager_notes: q.manager_notes ?? '',
    })
  }).catch((err) => setError(errorMessage(err, 'Failed to load quote')))

  useEffect(() => { load() }, [quoteId]) // eslint-disable-line react-hooks/exhaustive-deps

  if (error) return <p className="text-red-600 text-sm">{error}</p>
  if (!quote) return <p>Loading...</p>

  const update = (field) => (e) => setForm((f) => ({ ...f, [field]: e.target.value }))
  const updateConvert = (field) => (e) => setConvertForm((f) => ({ ...f, [field]: e.target.value }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      const payload = {
        status: form.status,
        proposed_price: form.proposed_price === '' ? null : Number(form.proposed_price),
        currency: form.currency || null,
        valid_until: form.valid_until ? new Date(form.valid_until).toISOString() : null,
        manager_notes: form.manager_notes || null,
      }
      await adminUpdateQuote(quote.id, payload)
      await load()
    } catch (err) {
      setError(errorMessage(err, 'Failed to update quote'))
    } finally {
      setSubmitting(false)
    }
  }

  const handleConvert = async (e) => {
    e.preventDefault()
    setConvertError(null)
    setConvertSubmitting(true)
    try {
      const order = await adminConvertQuote(quote.id, convertForm)
      navigate(`/admin/orders/${order.id}`)
    } catch (err) {
      setConvertError(errorMessage(err, 'Failed to convert quote'))
    } finally {
      setConvertSubmitting(false)
    }
  }

  const canConvert = quote.status === 'accepted' && !quote.order_id && quote.proposed_price != null

  return (
    <div>
      <Link to="/admin/quotes" className="text-sm text-brand">&larr; Back to quotes</Link>
      <h1 className="text-2xl font-bold mt-2 mb-1">{quote.rfq_number ?? `Quote #${quote.id}`}</h1>
      <p className="text-sm text-gray-500 mb-6">{quote.request_type} · {quote.name} · {quote.email}</p>

      <div className="grid md:grid-cols-2 gap-8">
        <div>
          <dl className="text-sm space-y-2 mb-6">
            <div><dt className="text-gray-500">Company</dt><dd>{quote.company ?? '—'}</dd></div>
            <div><dt className="text-gray-500">Country / City</dt><dd>{quote.country}{quote.city ? `, ${quote.city}` : ''}</dd></div>
            <div><dt className="text-gray-500">Phone</dt><dd>{quote.phone ?? '—'}</dd></div>
            <div><dt className="text-gray-500">Products</dt><dd>{quote.products ?? '—'}</dd></div>
            <div><dt className="text-gray-500">Quantity</dt><dd>{quote.quantity ?? '—'}</dd></div>
            <div><dt className="text-gray-500">Comment</dt><dd className="whitespace-pre-line">{quote.comment ?? '—'}</dd></div>
            {quote.order_id && (
              <div><dt className="text-gray-500">Converted order</dt><dd><Link to={`/admin/orders/${quote.order_id}`} className="text-brand">View order</Link></dd></div>
            )}
          </dl>

          {canConvert && (
            <form onSubmit={handleConvert} className="border border-gray-200 rounded-lg p-4">
              <h2 className="font-semibold mb-3">Convert to order</h2>
              <input required placeholder="Address" value={convertForm.address_line} onChange={updateConvert('address_line')} className="w-full border border-gray-300 rounded px-3 py-2 text-sm mb-2" />
              <input required placeholder="Postal code" value={convertForm.postal_code} onChange={updateConvert('postal_code')} className="w-full border border-gray-300 rounded px-3 py-2 text-sm mb-2" />
              <input placeholder="Delivery method" value={convertForm.delivery_method} onChange={updateConvert('delivery_method')} className="w-full border border-gray-300 rounded px-3 py-2 text-sm mb-2" />
              <input placeholder="Payment method" value={convertForm.payment_method} onChange={updateConvert('payment_method')} className="w-full border border-gray-300 rounded px-3 py-2 text-sm mb-2" />
              {convertError && <p className="text-sm text-red-600 mb-2">{convertError}</p>}
              <button type="submit" disabled={convertSubmitting} className="bg-brand text-white rounded px-4 py-2 text-sm font-medium disabled:opacity-40">
                {convertSubmitting ? 'Converting...' : 'Convert to Order'}
              </button>
            </form>
          )}
        </div>

        <form onSubmit={handleSubmit} className="border border-gray-200 rounded-lg p-4 h-fit">
          <h2 className="font-semibold mb-3">Update quote</h2>
          <label className="block text-xs text-gray-500 mb-1">Status</label>
          <select value={form.status} onChange={update('status')} className="w-full border border-gray-300 rounded px-3 py-2 text-sm mb-3">
            {STATUSES.map((s) => <option key={s} value={s}>{s}</option>)}
          </select>
          <label className="block text-xs text-gray-500 mb-1">Proposed price</label>
          <div className="grid grid-cols-2 gap-2 mb-3">
            <input type="number" step="0.01" min="0" value={form.proposed_price} onChange={update('proposed_price')} placeholder="Price" className="border border-gray-300 rounded px-3 py-2 text-sm" />
            <input value={form.currency} onChange={update('currency')} placeholder="Currency (e.g. USD)" maxLength={3} className="border border-gray-300 rounded px-3 py-2 text-sm" />
          </div>
          <label className="block text-xs text-gray-500 mb-1">Valid until</label>
          <input type="date" value={form.valid_until} onChange={update('valid_until')} className="w-full border border-gray-300 rounded px-3 py-2 text-sm mb-3" />
          <label className="block text-xs text-gray-500 mb-1">Manager notes</label>
          <textarea value={form.manager_notes} onChange={update('manager_notes')} rows={3} className="w-full border border-gray-300 rounded px-3 py-2 text-sm mb-3" />
          {error && <p className="text-sm text-red-600 mb-2">{error}</p>}
          <button type="submit" disabled={submitting} className="bg-brand text-white rounded px-4 py-2 text-sm font-medium disabled:opacity-40">
            {submitting ? 'Saving...' : 'Save'}
          </button>
        </form>
      </div>
    </div>
  )
}
