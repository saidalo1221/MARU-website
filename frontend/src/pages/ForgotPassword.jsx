import { useState } from 'react'
import { Link } from 'react-router-dom'
import { forgotPassword } from '../api/auth'
import { useLocale } from '../context/LocaleContext'
import Seo from '../components/Seo'

export default function ForgotPassword() {
  const { t } = useLocale()
  const [email, setEmail] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [sent, setSent] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setSubmitting(true)
    try {
      await forgotPassword(email)
    } finally {
      // Backend always answers the same way regardless of whether the email
      // exists, so the UI shows the same confirmation either way.
      setSubmitting(false)
      setSent(true)
    }
  }

  if (sent) {
    return (
      <div className="max-w-sm mx-auto px-4 py-12 text-center">
        <Seo title={t('forgotPassword.title')} noindex />
        <h1 className="text-2xl font-bold mb-4">{t('forgotPassword.title')}</h1>
        <p className="text-sm text-gray-600">{t('forgotPassword.sent')}</p>
        <Link to="/login" className="text-brand text-sm mt-4 inline-block">{t('login.title')}</Link>
      </div>
    )
  }

  return (
    <div className="max-w-sm mx-auto px-4 py-12">
      <Seo title={t('forgotPassword.title')} noindex />
      <h1 className="text-2xl font-bold mb-2">{t('forgotPassword.title')}</h1>
      <p className="text-sm text-gray-500 mb-6">{t('forgotPassword.subtitle')}</p>
      <form onSubmit={handleSubmit} className="space-y-3">
        <input
          required
          type="email"
          placeholder={t('checkout.email')} aria-label={t('checkout.email')}
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="w-full border border-gray-300 rounded px-3 py-2 text-sm"
        />
        <button
          type="submit"
          disabled={submitting}
          className="w-full bg-brand text-white rounded py-2.5 font-medium disabled:opacity-40"
        >
          {submitting ? t('forgotPassword.submitting') : t('forgotPassword.submit')}
        </button>
      </form>
      <p className="text-sm text-gray-500 mt-4">
        <Link to="/login" className="text-brand underline">{t('forgotPassword.backToLogin')}</Link>
      </p>
    </div>
  )
}
