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

  if (state === 'done') return <p role="status" className="mt-4 text-white">{t('newsletter.checkEmail')}</p>

  return (
    <form onSubmit={submit} className="mt-6">
      <label htmlFor="newsletter-email" className="mb-2 block font-semibold text-white">{t('newsletter.title')}</label>
      <div className="flex flex-wrap gap-2">
        <input
          id="newsletter-email"
          type="email"
          required
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder={t('newsletter.placeholder')}
          className="min-w-[8rem] flex-1 rounded-full border border-white/30 bg-white/10 px-4 py-2 text-sm text-white placeholder:text-white/60"
        />
        <button type="submit" disabled={state === 'sending'} className="rounded-full bg-white/95 px-5 py-2 text-sm font-semibold text-ink transition hover:bg-white disabled:opacity-40">
          {t('newsletter.subscribe')}
        </button>
      </div>
      {state === 'error' && <p role="alert" className="mt-1 text-xs text-red-300">{error}</p>}
    </form>
  )
}
