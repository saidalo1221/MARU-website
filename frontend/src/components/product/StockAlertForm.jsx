import { useState } from 'react'
import { ApiError, apiRequest } from '../../api/client'
import { useAuth } from '../../context/AuthContext'
import { useLocale } from '../../context/LocaleContext'

// "Notify me when available" for an out-of-stock SKU. Signed-in customers
// don't need to type an email; the server uses the account address.
export default function StockAlertForm({ skuId }) {
  const { t } = useLocale()
  const { user } = useAuth()
  const [email, setEmail] = useState('')
  const [state, setState] = useState('idle') // idle | sending | done | error
  const [error, setError] = useState('')

  const submit = async (e) => {
    e.preventDefault()
    setState('sending')
    try {
      await apiRequest('/stock-alerts/', {
        method: 'POST',
        body: { sku_id: skuId, ...(user ? {} : { email: email.trim() }) },
      })
      setState('done')
    } catch (err) {
      if (err instanceof ApiError && err.status === 409) setError(t('stockAlert.inStock'))
      else if (err instanceof ApiError && err.status === 429) setError(t('stockAlert.tooMany'))
      else setError(t('stockAlert.failed'))
      setState('error')
    }
  }

  if (state === 'done') return <p role="status" className="mt-3 text-sm text-green-700">{t('stockAlert.done')}</p>

  return (
    <form onSubmit={submit} className="mt-3 border border-gray-200 rounded p-3">
      <p className="text-sm font-medium mb-2">{t('stockAlert.title')}</p>
      <div className="flex gap-2">
        {!user && (
          <input
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder={t('stockAlert.placeholder')}
            aria-label={t('stockAlert.placeholder')}
            className="min-w-0 flex-1 border border-gray-300 rounded px-2 py-1.5 text-sm"
          />
        )}
        <button type="submit" disabled={state === 'sending'} className="border border-brand text-brand rounded px-3 py-1.5 text-sm disabled:opacity-40">
          {t('stockAlert.button')}
        </button>
      </div>
      {state === 'error' && <p role="alert" className="text-xs text-red-600 mt-1">{error}</p>}
    </form>
  )
}
