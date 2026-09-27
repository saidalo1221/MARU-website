import { createContext, useContext, useEffect, useState } from 'react'
import { listExchangeRates } from '../api/exchangeRates'
import { useCart } from './CartContext'
import { convertAmount } from '../lib/currency'

const AdminCurrencyContext = createContext(null)

// Fetches the exchange rate table once for the whole admin section and
// exposes a convert() that turns any (amount, currency) into the header's
// currently selected display currency (the same CurrencySwitcher the
// storefront uses — cart.currency), matching how catalog/wishlist prices
// already convert. Falls back to the original amount/currency when no rate
// is configured, never fabricating a number.
export function AdminCurrencyProvider({ children }) {
  const { cart } = useCart()
  const [rates, setRates] = useState(null)
  const displayCurrency = cart?.currency || 'USD'

  useEffect(() => {
    listExchangeRates()
      .then((list) => {
        const map = {}
        list.forEach((r) => { map[r.currency] = Number(r.units_per_usd) })
        setRates(map)
      })
      .catch(() => setRates({}))
  }, [])

  const convert = (amount, fromCurrency) => {
    if (!rates) return null
    return convertAmount(amount, fromCurrency, displayCurrency, rates)
  }

  return (
    <AdminCurrencyContext.Provider value={{ displayCurrency, convert, ratesLoaded: rates !== null }}>
      {children}
    </AdminCurrencyContext.Provider>
  )
}

export function useAdminCurrency() {
  const ctx = useContext(AdminCurrencyContext)
  if (!ctx) throw new Error('useAdminCurrency must be used within AdminCurrencyProvider')
  return ctx
}
