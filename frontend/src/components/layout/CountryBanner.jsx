import { useEffect, useState } from 'react'
import { useLocale } from '../../context/LocaleContext'
import { useCart } from '../../context/CartContext'
import { listExchangeRates } from '../../api/exchangeRates'

// MARU's primary market (UzCloud-hosted, PRD default currency UZS) — no
// banner for visitors already there, only for everyone else.
const HOME_COUNTRY = 'UZ'

// Free geo-IP lookup, no API key, no new npm dependency — good enough for a
// storefront banner. Has a low daily rate limit on the free tier; swap for
// a paid geo-IP provider if traffic grows past it.
const GEO_IP_URL = 'https://ipapi.co/json/'

const DISMISS_KEY = 'maru_country_banner_dismissed'

// Only the currencies this storefront actually prices in (PRD section 14 /
// CurrencySwitcher) — everything else falls back to "no currency suggestion".
const COUNTRY_CURRENCY = {
  UZ: 'UZS',
  KZ: 'KZT',
  AE: 'AED',
  RU: 'RUB',
  US: 'USD',
  DE: 'EUR', FR: 'EUR', IT: 'EUR', ES: 'EUR', NL: 'EUR', BE: 'EUR', AT: 'EUR',
  PT: 'EUR', IE: 'EUR', FI: 'EUR', GR: 'EUR', LU: 'EUR', SK: 'EUR', SI: 'EUR',
  EE: 'EUR', LV: 'EUR', LT: 'EUR', CY: 'EUR', MT: 'EUR', HR: 'EUR',
}

export default function CountryBanner() {
  const { t } = useLocale()
  const { cart, setCurrency } = useCart()
  const [country, setCountry] = useState(null)
  const [availableCurrencies, setAvailableCurrencies] = useState(['USD'])
  const [dismissed, setDismissed] = useState(true)

  useEffect(() => {
    try {
      if (localStorage.getItem(DISMISS_KEY) === '1') return
    } catch {
      // localStorage unavailable (private mode etc.) — fall through and just
      // won't persist the dismissal.
    }
    setDismissed(false)

    fetch(GEO_IP_URL)
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (data?.country_code) setCountry({ code: data.country_code, name: data.country_name || data.country_code })
      })
      .catch(() => {})

    listExchangeRates()
      .then((rates) => setAvailableCurrencies(['USD', ...rates.map((r) => r.currency)]))
      .catch(() => {})
  }, [])

  const dismiss = () => {
    setDismissed(true)
    try {
      localStorage.setItem(DISMISS_KEY, '1')
    } catch {
      // ignore — worst case the banner reappears next visit
    }
  }

  if (dismissed || !country || !cart || country.code === HOME_COUNTRY) return null

  const suggestedCurrency = COUNTRY_CURRENCY[country.code]
  const canSwitchCurrency =
    suggestedCurrency && suggestedCurrency !== cart.currency && availableCurrencies.includes(suggestedCurrency)

  return (
    <div className="bg-blue-50 border-b border-blue-200 text-blue-900 text-sm px-4 py-2 flex flex-wrap items-center justify-center gap-2 text-center">
      <span>{t('countryBanner.message', { country: country.name })}</span>
      <span className="text-blue-700">{t('countryBanner.shippingNote')}</span>
      {canSwitchCurrency && (
        <button onClick={() => setCurrency(suggestedCurrency)} className="underline font-medium">
          {t('countryBanner.switchCurrency', { currency: suggestedCurrency })}
        </button>
      )}
      <button onClick={dismiss} className="text-blue-500 hover:text-blue-700 ml-1" aria-label={t('countryBanner.dismiss')}>
        ✕
      </button>
    </div>
  )
}
