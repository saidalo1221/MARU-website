import { useAdminCurrency } from '../../context/AdminCurrencyContext'
import { formatMoney } from '../../lib/currency'

// showOriginal=true is for historical financial records (order/quote/refund
// amounts) — what was actually charged/settled must stay visible, so the
// converted figure is shown as an at-a-glance approximation alongside it,
// never in place of it. showOriginal=false (the default) is for config-type
// values (SKU prices, promo/shipping/tax amounts) where the storefront
// itself only ever shows one converted number, so the admin view matches.
export default function Money({ amount, currency, showOriginal = false }) {
  const { displayCurrency, convert, ratesLoaded } = useAdminCurrency()

  if (amount == null) return <span>—</span>

  if (currency === displayCurrency || !ratesLoaded) {
    return <span>{formatMoney(amount, currency)}</span>
  }

  const converted = convert(amount, currency)
  if (converted == null) {
    // No exchange rate configured for this currency — show the real value
    // rather than silently failing to convert.
    return <span>{formatMoney(amount, currency)}</span>
  }

  if (showOriginal) {
    return (
      <span>
        {formatMoney(converted, displayCurrency)}{' '}
        <span className="text-gray-400 text-xs">({formatMoney(amount, currency)})</span>
      </span>
    )
  }

  return <span>{formatMoney(converted, displayCurrency)}</span>
}
