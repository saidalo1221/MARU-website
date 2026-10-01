import { useState } from 'react'
import { ApiError } from '../../api/client'
import { subscribeNewsletter } from '../../api/newsletter'
import { useLocale } from '../../context/LocaleContext'

// Footer signup. The server answers identically whether or not the address
// was already subscribed, so the success message never reveals list membership.
export default function NewsletterForm() {
  const { t, locale } = useLocale()
  const [email, setEmail] = useState('')
  const [state, setState] = useState('idle') // idle | sending | done | error
  const [error, setError] = useState('')

  const submit = async (e) => {
    e.preventDefault()
    setState('sending')
    try {
      await subscribeNewsletter(email.trim(), locale)
      setState('done')
    } catch (err) {
      setError(err instanceof ApiError && err.status === 429 ? t('newsletter.tooMany') : t('newsletter.failed'))
      setState('error')
    }
  }

  if (state === 'done') return <p role="status" className="mt-3 text-green-700">{t('newsletter.checkEmail')}</p>

  return (
    <form onSubmit={submit} className="mt-3">
      <label htmlFor="newsletter-email" className="font-semibold text-gray-900 block mb-1">{t('newsletter.title')}</label>
      <div className="flex flex-wrap gap-1">
        <input
          id="newsletter-email"
          type="email"
          required
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder={t('newsletter.placeholder')}
          className="min-w-[8rem] flex-1 border border-gray-300 rounded px-2 py-1.5 text-sm"
        />
        <button type="submit" disabled={state === 'sending'} className="bg-brand text-white rounded px-3 py-1.5 text-sm disabled:opacity-40">
          {t('newsletter.subscribe')}
        </button>
      </div>
      {state === 'error' && <p role="alert" className="text-xs text-red-600 mt-1">{error}</p>}
    </form>
  )
}
