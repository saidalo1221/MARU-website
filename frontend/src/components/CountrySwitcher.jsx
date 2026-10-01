import { useEffect, useState } from 'react'
import { listShippingCountries } from '../api/shipping'
import { useLocale } from '../context/LocaleContext'
import { setShipCountry, useShipCountry } from '../lib/shipCountry'

// Country | Language | Currency (PRD ТЗ№2 §41). The country is where the
// order is delivered; it never blocks browsing (§42).
export default function CountrySwitcher({ className = '' }) {
  const { t } = useLocale()
  const country = useShipCountry()
  const [countries, setCountries] = useState([])

  useEffect(() => {
    listShippingCountries().then(setCountries).catch(() => {})
  }, [])

  if (countries.length === 0) return null

  return (
    <select
      value={country}
      onChange={(e) => setShipCountry(e.target.value)}
      className={`bg-transparent text-sm border border-gray-300 rounded px-2 py-1 ${className}`}
      aria-label={t('header.country')}
    >
      <option value="">{t('header.anyCountry')}</option>
      {countries.map((c) => <option key={c} value={c}>{c}</option>)}
    </select>
  )
}
