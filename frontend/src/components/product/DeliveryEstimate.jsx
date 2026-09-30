import { useEffect, useState } from 'react'
import { getShippingEstimate, listShippingCountries } from '../../api/shipping'
import { useLocale } from '../../context/LocaleContext'

const KEY = 'maru_ship_country'

function readCountry() {
  try {
    return localStorage.getItem(KEY) || ''
  } catch {
    return ''
  }
}

// "Delivery in 2-5 days to <country>" (PRD ТЗ№2 §29). Shows nothing until an
// admin has entered delivery days on a shipping rate.
export default function DeliveryEstimate() {
  const { t } = useLocale()
  const [countries, setCountries] = useState([])
  const [country, setCountry] = useState(readCountry)
  const [estimate, setEstimate] = useState(null)

  useEffect(() => {
    listShippingCountries().then(setCountries).catch(() => {})
  }, [])

  useEffect(() => {
    getShippingEstimate(country).then(setEstimate).catch(() => setEstimate(null))
  }, [country])

  const choose = (e) => {
    setCountry(e.target.value)
    try {
      localStorage.setItem(KEY, e.target.value)
    } catch {
      // storage blocked: the choice just isn't remembered
    }
  }

  if (!estimate || estimate.max_days == null) return null

  const days = estimate.min_days != null && estimate.min_days !== estimate.max_days
    ? `${estimate.min_days}–${estimate.max_days}`
    : `${estimate.max_days}`

  return (
    <div className="mt-3 text-sm">
      <p>{t('productDetail.deliveryEstimate', { days })}</p>
      {estimate.free_shipping_threshold != null && (
        <p className="text-green-700">
          {t('productDetail.freeShippingOver', { amount: `${estimate.currency} ${Number(estimate.free_shipping_threshold).toFixed(0)}` })}
        </p>
      )}
      {countries.length > 0 && (
        <label className="block mt-1 text-xs text-gray-500">
          {t('productDetail.deliverTo')}{' '}
          <select value={country} onChange={choose} className="border border-gray-300 rounded px-1 py-0.5 text-xs">
            <option value="">{t('productDetail.anyCountry')}</option>
            {countries.map((c) => <option key={c} value={c}>{c}</option>)}
          </select>
        </label>
      )}
    </div>
  )
}
