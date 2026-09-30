import { useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { useLocale } from '../context/LocaleContext'
import { errorMessage } from '../api/client'
import PasswordInput from '../components/PasswordInput'
import Seo from '../components/Seo'
import LegalNotice from '../components/LegalNotice'

const emptyForm = { email: '', password: '', first_name: '', last_name: '', phone: '' }

export default function Register() {
  const { register } = useAuth()
  const { t } = useLocale()
  const navigate = useNavigate()
  const [params] = useSearchParams()
  const next = params.get('next') || '/account/orders'
  const [form, setForm] = useState(emptyForm)
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
    <div className="max-w-sm mx-auto px-4 py-12">
      <Seo title={t('register.title')} noindex />
      <h1 className="text-2xl font-bold mb-6">{t('register.title')}</h1>
      <form onSubmit={handleSubmit} className="space-y-3">
        <input required placeholder={t('checkout.firstName')} aria-label={t('checkout.firstName')} value={form.first_name} onChange={update('first_name')} className="w-full border border-gray-300 rounded px-3 py-2 text-sm" />
        <input required placeholder={t('checkout.lastName')} aria-label={t('checkout.lastName')} value={form.last_name} onChange={update('last_name')} className="w-full border border-gray-300 rounded px-3 py-2 text-sm" />
        <input placeholder={t('checkout.phone')} aria-label={t('checkout.phone')} value={form.phone} onChange={update('phone')} className="w-full border border-gray-300 rounded px-3 py-2 text-sm" />
        <input required type="email" placeholder={t('checkout.email')} aria-label={t('checkout.email')} value={form.email} onChange={update('email')} className="w-full border border-gray-300 rounded px-3 py-2 text-sm" />
        <PasswordInput required placeholder={t('login.password')} value={form.password} onChange={update('password')} className="w-full border border-gray-300 rounded px-3 py-2 text-sm" />
        {error && <p role="alert" className="text-sm text-red-600">{error}</p>}
        <button type="submit" disabled={submitting} className="w-full bg-brand text-white rounded py-2.5 font-medium disabled:opacity-40">
          {submitting ? t('register.submitting') : t('register.submit')}
        </button>
        <LegalNotice />
      </form>
      <p className="text-sm text-gray-500 mt-4">
        {t('register.haveAccount')} <Link to={`/login?next=${encodeURIComponent(next)}`} className="text-brand underline">{t('register.login')}</Link>
      </p>
    </div>
  )
}
