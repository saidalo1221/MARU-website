import { useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { useLocale } from '../context/LocaleContext'
import { errorMessage } from '../api/client'
import PasswordInput from '../components/PasswordInput'
import AuthSplit, { authButtonClass, authInputClass } from '../components/auth/AuthSplit'
import Seo from '../components/Seo'

export default function Login() {
  const { login, verifyDevice } = useAuth()
  const { t } = useLocale()
  const navigate = useNavigate()
  const [params] = useSearchParams()
  const next = params.get('next') || '/account/orders'
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [code, setCode] = useState('')
  const [phase, setPhase] = useState('credentials') // credentials | device-code
  const [error, setError] = useState(null)
  const [submitting, setSubmitting] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      const result = await login(email, password)
      if (result.device_verification_required) {
        setPhase('device-code')
      } else {
        navigate(next)
      }
    } catch (err) {
      setError(errorMessage(err, t('login.failed')))
    } finally {
      setSubmitting(false)
    }
  }

  const handleVerifyDevice = async (e) => {
    e.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      await verifyDevice(email, code)
      navigate(next)
    } catch (err) {
      setError(errorMessage(err, t('login.deviceCodeFailed')))
    } finally {
      setSubmitting(false)
    }
  }

  if (phase === 'device-code') {
    return (
      <AuthSplit title={t('login.deviceCodeTitle')} description={t('login.deviceCodeSubtitle', { email })}>
        <form onSubmit={handleVerifyDevice} className="space-y-5">
          <input
            required
            inputMode="numeric"
            pattern="[0-9]*"
            placeholder={t('login.deviceCodePlaceholder')} aria-label={t('login.deviceCodePlaceholder')}
            value={code}
            onChange={(e) => setCode(e.target.value)}
            className={`${authInputClass} tracking-widest text-center text-lg`}
          />
          {error && <p role="alert" className="text-sm text-red-600">{error}</p>}
          <button type="submit" disabled={submitting} className={authButtonClass}>
            {submitting ? t('login.submitting') : t('login.deviceCodeVerify')}
          </button>
          <button
            type="button"
            onClick={() => { setPhase('credentials'); setCode(''); setError(null) }}
            className="w-full text-sm text-gray-500"
          >
            {t('admin.login.back')}
          </button>
        </form>
      </AuthSplit>
    )
  }

  return (
    <AuthSplit title={t('login.title')} description={t('login.subtitle')}>
      <Seo title={t('login.title')} noindex />
      <form onSubmit={handleSubmit} className="space-y-5">
        <input required type="text" inputMode="email" autoComplete="username" placeholder={t('login.identifier')} aria-label={t('login.identifier')} value={email} onChange={(e) => setEmail(e.target.value)} className={authInputClass} />
        <PasswordInput required placeholder={t('login.password')} value={password} onChange={(e) => setPassword(e.target.value)} className={authInputClass} />
        <div className="text-right">
          <Link to="/forgot-password" className="text-sm text-brand hover:underline">{t('forgotPassword.link')}</Link>
        </div>
        {error && <p role="alert" className="text-sm text-red-600">{error}</p>}
        <button type="submit" disabled={submitting} className={authButtonClass}>
          {submitting ? t('login.submitting') : t('login.submit')}
        </button>
      </form>
      <p className="text-center text-sm text-gray-500 mt-6">
        {t('login.noAccount')} <Link to={`/register?next=${encodeURIComponent(next)}`} className="text-brand hover:underline">{t('login.register')}</Link>
      </p>
    </AuthSplit>
  )
}
