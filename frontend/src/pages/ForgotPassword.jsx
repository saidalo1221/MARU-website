import { useState } from 'react'
import { Link } from 'react-router-dom'
import { forgotPassword } from '../api/auth'
import { ApiError, errorMessage } from '../api/client'
import { useLocale } from '../context/LocaleContext'
import AuthSplit, { authButtonClass, authInputClass } from '../components/auth/AuthSplit'
import Seo from '../components/Seo'

export default function ForgotPassword() {
  const { t } = useLocale()
  const [email, setEmail] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [sent, setSent] = useState(false)
  const [error, setError] = useState(null)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      await forgotPassword(email)
      // The backend answers the same way whether or not the email has an account,
      // so this confirmation never reveals which addresses are registered.
      setSent(true)
    } catch (err) {
      // A failed request (server unreachable, too many attempts) must not look like success.
      setError(err instanceof ApiError ? errorMessage(err, t('login.networkError')) : t('login.networkError'))
    } finally {
      setSubmitting(false)
    }
  }

  if (sent) {
    return (
      <AuthSplit title={t('forgotPassword.title')} description={t('forgotPassword.sent')}>
        <Seo title={t('forgotPassword.title')} noindex />
        <Link to="/login" className={`${authButtonClass} block text-center`}>{t('login.title')}</Link>
      </AuthSplit>
    )
  }

  return (
    <AuthSplit title={t('forgotPassword.title')} description={t('forgotPassword.subtitle')}>
      <Seo title={t('forgotPassword.title')} noindex />
      <form onSubmit={handleSubmit} className="space-y-5">
        <input
          required
          type="email"
          placeholder={t('checkout.email')} aria-label={t('checkout.email')}
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className={authInputClass}
        />
        {error && <p role="alert" className="text-sm text-red-600">{error}</p>}
        <button type="submit" disabled={submitting} className={authButtonClass}>
          {submitting ? t('forgotPassword.submitting') : t('forgotPassword.submit')}
        </button>
      </form>
      <p className="mt-6 text-center text-sm text-gray-500">
        <Link to="/login" className="text-brand hover:underline">{t('forgotPassword.backToLogin')}</Link>
      </p>
    </AuthSplit>
  )
}
