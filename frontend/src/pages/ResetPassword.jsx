import { useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { resetPassword } from '../api/auth'
import { useLocale } from '../context/LocaleContext'
import { errorMessage } from '../api/client'
import PasswordInput from '../components/PasswordInput'
import AuthSplit, { authButtonClass, authInputClass } from '../components/auth/AuthSplit'
import Seo from '../components/Seo'

export default function ResetPassword() {
  const { t } = useLocale()
  const navigate = useNavigate()
  const [params] = useSearchParams()
  const token = params.get('token') || ''
  const [password, setPassword] = useState('')
  const [error, setError] = useState(null)
  const [submitting, setSubmitting] = useState(false)
  const [done, setDone] = useState(false)

  if (!token) {
    return (
      <AuthSplit title={t('resetPassword.title')}>
        <Seo title={t('resetPassword.title')} noindex />
        <p role="alert" className="mb-5 rounded-2xl border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-800">{t('resetPassword.missingToken')}</p>
        <Link to="/forgot-password" className={`${authButtonClass} block text-center`}>{t('resetPassword.requestNew')}</Link>
      </AuthSplit>
    )
  }

  if (done) {
    return (
      <AuthSplit title={t('resetPassword.title')} description={t('resetPassword.success')}>
        <Seo title={t('resetPassword.title')} noindex />
        <button onClick={() => navigate('/login')} className={authButtonClass}>
          {t('login.title')}
        </button>
      </AuthSplit>
    )
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      await resetPassword(token, password)
      setDone(true)
    } catch (err) {
      setError(errorMessage(err, t('resetPassword.failed')))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <AuthSplit title={t('resetPassword.title')} description={t('resetPassword.subtitle')}>
      <Seo title={t('resetPassword.title')} noindex />
      <form onSubmit={handleSubmit} className="space-y-5">
        <PasswordInput
          required
          minLength={8}
          autoComplete="new-password"
          placeholder={t('resetPassword.newPassword')}
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className={authInputClass}
        />
        {error && <p role="alert" className="text-sm text-red-600">{error}</p>}
        <button type="submit" disabled={submitting} className={authButtonClass}>
          {submitting ? t('resetPassword.submitting') : t('resetPassword.submit')}
        </button>
      </form>
    </AuthSplit>
  )
}
