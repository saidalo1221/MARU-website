import { useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { ApiError } from '../api/client'
import { trackOrder } from '../api/orders'
import { useLocale } from '../context/LocaleContext'
import Seo from '../components/Seo'
import ShipmentList from '../components/ShipmentList'

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
    <div className="max-w-xl mx-auto px-4 py-8">
      <Seo title={t('track.title')} noindex />
      <h1 className="text-2xl font-bold mb-2">{t('track.title')}</h1>
      <p className="text-gray-500 text-sm mb-6">{t('track.intro')}</p>

      <form onSubmit={handleSubmit} className="space-y-3 mb-8">
        <input
          required
          value={orderNumber}
          onChange={(e) => setOrderNumber(e.target.value)}
          placeholder="MARU-20260930-ABC123"
          aria-label={t('track.orderNumber')}
          className="w-full border border-gray-300 rounded px-3 py-2 text-sm"
        />
        <input
          required
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder={t('track.email')}
          aria-label={t('track.email')}
          className="w-full border border-gray-300 rounded px-3 py-2 text-sm"
        />
        <button type="submit" disabled={loading} className="bg-brand text-white rounded px-4 py-2 text-sm font-medium disabled:opacity-40">
          {loading ? t('track.searching') : t('track.submit')}
        </button>
      </form>

      {error && <p role="alert" className="text-sm text-red-600">{error}</p>}

      {result && (
        <div role="status">
          <p className="font-semibold">{result.order_number}</p>
          <p className="text-sm text-gray-500 mb-4">
            {t('track.status')}: <span className="text-gray-900 font-medium">{t(`orderStatus.statusLabels.${result.status}`)}</span>
          </p>
          <ShipmentList shipments={result.shipments} />
        </div>
      )}
    </div>
  )
}
