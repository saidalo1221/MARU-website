import { useEffect, useState } from 'react'
import { getShippingEstimate, listShippingCountries } from '../../api/shipping'
import { useLocale } from '../../context/LocaleContext'
import { setShipCountry, useShipCountry } from '../../lib/shipCountry'

// Delivery block of the product page (PRD ТЗ№2 §17): whether MARU delivers to
// the chosen country, how long it takes, what it costs, and a country selector.
export default function DeliveryEstimate() {
  const { t } = useLocale()
  const [countries, setCountries] = useState([])
  const country = useShipCountry()
  const [estimate, setEstimate] = useState(null)

  useEffect(() => {
    listShippingCountries().then(setCountries).catch(() => {})
  }, [])

  useEffect(() => {
    getShippingEstimate(country).then(setEstimate).catch(() => setEstimate(null))
  }, [country])

  if (countries.length === 0 && !estimate?.available) return null

  const hasDays = estimate && estimate.max_days != null
  const days = hasDays
    ? (estimate.min_days != null && estimate.min_days !== estimate.max_days ? `${estimate.min_days}–${estimate.max_days}` : `${estimate.max_days}`)
    : null
  const fee = estimate?.from_fee != null ? Number(estimate.from_fee) : null

  return (
    <div className="mt-3 text-sm">
      {country && estimate && !estimate.available && (
        <p className="text-red-600">{t('productDetail.deliveryNotAvailable', { country })}</p>
      )}
      {estimate?.available && (
        <>
          {country && <p className="font-medium">{t('productDetail.deliveryTo', { country })}</p>}
          {days && <p>{t('productDetail.deliveryEstimate', { days })}</p>}
          {fee != null && (
            <p>
              {fee === 0
                ? t('productDetail.deliveryFree')
                : t('productDetail.deliveryFrom', { amount: `${estimate.fee_currency} ${fee.toFixed(2)}` })}
            </p>
          )}
          {estimate.free_shipping_threshold != null && (
            <p className="text-green-700">
              {t('productDetail.freeShippingOver', { amount: `${estimate.currency} ${Number(estimate.free_shipping_threshold).toFixed(0)}` })}
            </p>
          )}
        </>
      )}
      {countries.length > 0 && (
        <label className="block mt-1 text-xs text-gray-500">
          {t('productDetail.deliverTo')}{' '}
          <select value={country} onChange={(e) => setShipCountry(e.target.value)} className="border border-gray-300 rounded px-1 py-0.5 text-xs">
            <option value="">{t('productDetail.anyCountry')}</option>
            {countries.map((c) => <option key={c} value={c}>{c}</option>)}
          </select>
        </label>
      )}
    </div>
  )
}
