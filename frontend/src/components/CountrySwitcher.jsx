import { useEffect, useState } from 'react'
import { listExchangeRates } from '../api/exchangeRates'
import { listShippingCountries } from '../api/shipping'
import { useCart } from '../context/CartContext'
import { useLocale } from '../context/LocaleContext'
import { setShipCountry, useShipCountry } from '../lib/shipCountry'

// The usual currency of the countries MARU ships to (PRD ТЗ№2 §41: choosing
// Germany shows EUR). Only used to suggest a switch, and only to a currency
// the store actually prices in.
const COUNTRY_CURRENCY = {
  uzbekistan: 'UZS',
  kazakhstan: 'KZT',
  'united arab emirates': 'AED',
  uae: 'AED',
  'south korea': 'KRW',
  korea: 'KRW',
  russia: 'RUB',
  'united states': 'USD',
  usa: 'USD',
  germany: 'EUR', france: 'EUR', italy: 'EUR', spain: 'EUR', netherlands: 'EUR', belgium: 'EUR', austria: 'EUR',
  portugal: 'EUR', ireland: 'EUR', finland: 'EUR', greece: 'EUR',
}

// Country | Language | Currency (PRD ТЗ№2 §41). The country is where the
// order is delivered; it never blocks browsing (§42).
export default function CountrySwitcher({ className = '' }) {
  const { t } = useLocale()
  const { setCurrency } = useCart()
  const country = useShipCountry()
  const [countries, setCountries] = useState([])
  const [currencies, setCurrencies] = useState(['USD'])

  useEffect(() => {
    listShippingCountries().then(setCountries).catch(() => {})
    listExchangeRates().then((rates) => setCurrencies(['USD', ...rates.map((r) => r.currency)])).catch(() => {})
  }, [])

  if (countries.length === 0) return null

  const choose = (e) => {
    const value = e.target.value
    setShipCountry(value)
    const currency = COUNTRY_CURRENCY[value.trim().toLowerCase()]
    if (currency && currencies.includes(currency)) setCurrency(currency).catch(() => {})
  }

  return (
    <select
      value={country}
      onChange={choose}
      className={`bg-transparent text-sm border border-gray-300 rounded px-2 py-1 ${className}`}
      aria-label={t('header.country')}
    >
      <option value="">{t('header.anyCountry')}</option>
      {countries.map((c) => <option key={c} value={c}>{c}</option>)}
    </select>
  )
}
