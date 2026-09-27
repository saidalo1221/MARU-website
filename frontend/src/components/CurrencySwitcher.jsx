import { useState } from 'react'
import { useCart } from '../context/CartContext'
import { ApiError } from '../api/client'

const CANDIDATE_CURRENCIES = ['USD', 'UZS', 'EUR', 'KZT', 'AED']

export default function CurrencySwitcher() {
  const { cart, setCurrency } = useCart()
  const [error, setError] = useState(null)

  if (!cart) return null

  const handleChange = async (e) => {
    const value = e.target.value
    setError(null)
    try {
      await setCurrency(value)
    } catch (err) {
      if (err instanceof ApiError) setError('That currency is not available yet')
    }
  }

  return (
    <div className="relative">
      <select
        value={cart.currency}
        onChange={handleChange}
        className="bg-transparent text-sm border border-gray-300 rounded px-2 py-1"
        aria-label="Currency"
      >
        {CANDIDATE_CURRENCIES.map((code) => (
          <option key={code} value={code}>
            {code}
          </option>
        ))}
      </select>
      {error && <p className="absolute top-full left-0 text-xs text-red-600 whitespace-nowrap">{error}</p>}
    </div>
  )
}
