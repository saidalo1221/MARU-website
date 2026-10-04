import { useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { ApiError } from '../api/client'
import { trackOrder } from '../api/orders'
import { useLocale } from '../context/LocaleContext'
import PageIntro from '../components/layout/PageIntro'
import Seo from '../components/Seo'
import ShipmentList from '../components/ShipmentList'

const inputCls = 'w-full rounded-2xl border border-gray-300 bg-white px-4 py-3 text-sm'

export default function TrackOrder() {
  const { t } = useLocale()
  const [searchParams] = useSearchParams()
  // The order page links here with ?order=<number>; the email is still asked for.
  const [orderNumber, setOrderNumber] = useState(searchParams.get('order') || '')
  const [email, setEmail] = useState('')
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)
    setResult(null)
    setLoading(true)
    try {
      setResult(await trackOrder(orderNumber.trim(), email.trim()))
    } catch (err) {
      setError(err instanceof ApiError && err.status === 429 ? err.message : t('track.notFound'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-xl mx-auto px-4 py-12 md:py-16">
      <Seo title={t('track.title')} noindex />
      <PageIntro title={t('track.title')} subtitle={t('track.intro')} />

      <form onSubmit={handleSubmit} className="mb-8 space-y-4 rounded-3xl border border-gray-200 bg-gray-50 p-6 md:p-8">
        <input
          required
          value={orderNumber}
          onChange={(e) => setOrderNumber(e.target.value)}
          placeholder="MARU-20260930-ABC123"
          aria-label={t('track.orderNumber')}
          className={inputCls}
        />
        <input
          required
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder={t('track.email')}
          aria-label={t('track.email')}
          className={inputCls}
        />
        <button type="submit" disabled={loading} className="w-full rounded-full bg-brand py-3 font-semibold text-white transition-colors hover:bg-brand-dark disabled:opacity-40">
          {loading ? t('track.searching') : t('track.submit')}
        </button>
      </form>

      {error && <p role="alert" className="rounded-2xl border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-800">{error}</p>}

      {result && (
        <div role="status" className="rounded-3xl bg-brand-light p-6 md:p-8">
          <p className="text-lg font-semibold">{result.order_number}</p>
          <p className="mb-4 text-sm text-gray-600">
            {t('track.status')}: <span className="font-medium text-gray-900">{t(`orderStatus.statusLabels.${result.status}`)}</span>
          </p>
          <ShipmentList shipments={result.shipments} />
        </div>
      )}
    </div>
  )
}
