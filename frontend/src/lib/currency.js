// Mirrors app/services/currency.py's convert_amount() exactly (USD is the
// implicit base; `rates` is {currency: units_per_usd} from /exchange-rates/).
// Used only for admin-panel *display* conversion — writes always go back in
// the SKU/order's own native currency, never a converted one.
const BASE_CURRENCY = 'USD'

export function convertAmount(amount, fromCurrency, toCurrency, rates) {
  if (amount == null) return null
  if (fromCurrency === toCurrency) return Number(amount)

  const rateFrom = fromCurrency === BASE_CURRENCY ? 1 : rates[fromCurrency]
  const rateTo = toCurrency === BASE_CURRENCY ? 1 : rates[toCurrency]
  if (!rateFrom || !rateTo) return null // no rate configured — can't convert

  const usdAmount = Number(amount) / rateFrom
  return Math.round(usdAmount * rateTo * 100) / 100
}

export function formatMoney(amount, currency) {
  if (amount == null) return '—'
  return `${currency} ${Number(amount).toFixed(2)}`
}
