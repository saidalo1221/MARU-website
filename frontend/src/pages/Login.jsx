import { useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { useLocale } from '../context/LocaleContext'
import { ApiError } from '../api/client'
import PasswordInput from '../components/PasswordInput'

export default function Login() {
  const { login } = useAuth()
  const { t } = useLocale()
  const navigate = useNavigate()
  const [params] = useSearchParams()
  const next = params.get('next') || '/account/orders'
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState(null)
  const [submitting, setSubmitting] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      await login(email, password)
      navigate(next)
    } catch (err) {
      setError(err instanceof ApiError ? t('login.invalidCredentials') : t('login.failed'))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="max-w-sm mx-auto px-4 py-12">
      <h1 className="text-2xl font-bold mb-6">{t('login.title')}</h1>
      <form onSubmit={handleSubmit} className="space-y-3">
        <input required type="email" placeholder={t('checkout.email')} value={email} onChange={(e) => setEmail(e.target.value)} className="w-full border border-gray-300 rounded px-3 py-2 text-sm" />
        <PasswordInput required placeholder={t('login.password')} value={password} onChange={(e) => setPassword(e.target.value)} className="w-full border border-gray-300 rounded px-3 py-2 text-sm" />
        <div className="text-right">
          <Link to="/forgot-password" className="text-xs text-brand">{t('forgotPassword.link')}</Link>
        </div>
        {error && <p className="text-sm text-red-600">{error}</p>}
        <button type="submit" disabled={submitting} className="w-full bg-brand text-white rounded py-2.5 font-medium disabled:opacity-40">
          {submitting ? t('login.submitting') : t('login.submit')}
        </button>
      </form>
      <p className="text-sm text-gray-500 mt-4">
        {t('login.noAccount')} <Link to={`/register?next=${encodeURIComponent(next)}`} className="text-brand">{t('login.register')}</Link>
      </p>
    </div>
  )
}
