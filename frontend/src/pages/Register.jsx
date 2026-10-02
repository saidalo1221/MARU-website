import { useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { useLocale } from '../context/LocaleContext'
import { errorMessage } from '../api/client'
import PasswordInput from '../components/PasswordInput'
import AuthSplit, { authButtonClass, authInputClass } from '../components/auth/AuthSplit'
import Seo from '../components/Seo'
import LegalNotice from '../components/LegalNotice'

const emptyForm = { email: '', password: '', first_name: '', last_name: '', phone: '' }

export default function Register() {
  const { register } = useAuth()
  const { t } = useLocale()
  const navigate = useNavigate()
  const [params] = useSearchParams()
  const next = params.get('next') || '/account/orders'
  // The order page links here with ?email= after a guest checkout.
  const [form, setForm] = useState({ ...emptyForm, email: params.get('email') || '' })
  const [error, setError] = useState(null)
  const [submitting, setSubmitting] = useState(false)

  const update = (field) => (e) => setForm((f) => ({ ...f, [field]: e.target.value }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      await register(form)
      navigate(next)
    } catch (err) {
      setError(errorMessage(err, t('register.failed')))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <AuthSplit title={t('register.title')} description={t('register.subtitle')}>
      <Seo title={t('register.title')} noindex />
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-2 gap-3">
          <input required placeholder={t('checkout.firstName')} aria-label={t('checkout.firstName')} value={form.first_name} onChange={update('first_name')} className={authInputClass} />
          <input required placeholder={t('checkout.lastName')} aria-label={t('checkout.lastName')} value={form.last_name} onChange={update('last_name')} className={authInputClass} />
        </div>
        <input placeholder={t('checkout.phone')} aria-label={t('checkout.phone')} value={form.phone} onChange={update('phone')} className={authInputClass} />
        <input required type="email" placeholder={t('checkout.email')} aria-label={t('checkout.email')} value={form.email} onChange={update('email')} className={authInputClass} />
        <PasswordInput required placeholder={t('login.password')} value={form.password} onChange={update('password')} className={authInputClass} />
        {error && <p role="alert" className="text-sm text-red-600">{error}</p>}
        <button type="submit" disabled={submitting} className={authButtonClass}>
          {submitting ? t('register.submitting') : t('register.submit')}
        </button>
        <LegalNotice />
      </form>
      <p className="mt-6 text-center text-sm text-gray-500">
        {t('register.haveAccount')} <Link to={`/login?next=${encodeURIComponent(next)}`} className="text-brand hover:underline">{t('register.login')}</Link>
      </p>
    </AuthSplit>
  )
}
