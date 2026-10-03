import { useEffect, useRef, useState } from 'react'
import { Link, useParams, useSearchParams } from 'react-router-dom'
import { confirmNewsletter, unsubscribeNewsletter } from '../api/newsletter'
import { useLocale } from '../context/LocaleContext'
import Seo from '../components/Seo'

// Landing page for the links in newsletter emails: /newsletter/confirm?token=...
// and /newsletter/unsubscribe?token=...
export default function NewsletterAction() {
  const { t } = useLocale()
  const { action } = useParams()
  const [params] = useSearchParams()
  const token = params.get('token')
  const [state, setState] = useState('working') // working | done | error
  const started = useRef(false)

  useEffect(() => {
    if (started.current) return
    started.current = true
    const call = action === 'unsubscribe' ? unsubscribeNewsletter : action === 'confirm' ? confirmNewsletter : null
    if (!call || !token) {
      setState('error')
      return
    }
    call(token).then(() => setState('done')).catch(() => setState('error'))
  }, [action, token])

  const key = action === 'unsubscribe' ? 'unsubscribed' : 'confirmed'
  return (
    <div className="max-w-xl mx-auto px-4 py-12 text-center">
      <Seo title={t('newsletter.title')} noindex />
      {state === 'working' && <p>{t('newsletter.working')}</p>}
      {state === 'done' && <h1 role="status" className="text-xl font-bold">{t(`newsletter.${key}`)}</h1>}
      {state === 'error' && <h1 role="alert" className="text-xl font-bold text-red-600">{t('newsletter.invalidLink')}</h1>}
      <Link to="/" className="inline-block mt-6 text-brand underline">{t('notFound.backHome')}</Link>
    </div>
  )
}
