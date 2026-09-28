import { useEffect, useState } from 'react'
import { useCart } from '../context/CartContext'
import { useLocale } from '../context/LocaleContext'
import { ApiError } from '../api/client'
import { listExchangeRates } from '../api/exchangeRates'

// USD is the implicit base currency (app/services/currency.py) and never
// has its own ExchangeRate row, so it's always offered even if the admin
// hasn't configured any rates yet.
export default function CurrencySwitcher() {
  const { cart, setCurrency } = useCart()
  const { t } = useLocale()
  const [error, setError] = useState(null)
  const [currencies, setCurrencies] = useState(['USD'])

  useEffect(() => {
    listExchangeRates()
      .then((rates) => setCurrencies(['USD', ...rates.map((r) => r.currency)]))
      .catch(() => {})
  }, [])

  if (!cart) return null

  const handleChange = async (e) => {
    const value = e.target.value
    setError(null)
    try {
      await setCurrency(value)
    } catch (err) {
      if (err instanceof ApiError) setError(t('currency.notAvailable'))
    }
  }

  return (
    <div className="relative">
      <select
        value={cart.currency}
        onChange={handleChange}
        className="bg-transparent text-sm border border-gray-300 rounded px-2 py-1"
        aria-label={t('currency.ariaLabel')}
      >
        {currencies.map((code) => (
          <option key={code} value={code}>
            {code}
          </option>
        ))}
      </select>
      {error && <p className="absolute top-full left-0 text-xs text-red-600 whitespace-nowrap">{error}</p>}
    </div>
  )
}
