import { useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { resetPassword } from '../api/auth'
import { useLocale } from '../context/LocaleContext'
import { errorMessage } from '../api/client'

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
      <div className="max-w-sm mx-auto px-4 py-12 text-center">
        <p className="text-red-600 text-sm mb-4">{t('resetPassword.missingToken')}</p>
        <Link to="/forgot-password" className="text-brand text-sm">{t('resetPassword.requestNew')}</Link>
      </div>
    )
  }

  if (done) {
    return (
      <div className="max-w-sm mx-auto px-4 py-12 text-center">
        <h1 className="text-2xl font-bold mb-4">{t('resetPassword.title')}</h1>
        <p className="text-sm text-gray-600 mb-4">{t('resetPassword.success')}</p>
        <button onClick={() => navigate('/login')} className="bg-brand text-white px-6 py-2.5 rounded font-medium">
          {t('login.title')}
        </button>
      </div>
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
    <div className="max-w-sm mx-auto px-4 py-12">
      <h1 className="text-2xl font-bold mb-6">{t('resetPassword.title')}</h1>
      <form onSubmit={handleSubmit} className="space-y-3">
        <input
          required
          type="password"
          minLength={8}
          placeholder={t('resetPassword.newPassword')}
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="w-full border border-gray-300 rounded px-3 py-2 text-sm"
        />
        {error && <p className="text-sm text-red-600">{error}</p>}
        <button
          type="submit"
          disabled={submitting}
          className="w-full bg-brand text-white rounded py-2.5 font-medium disabled:opacity-40"
        >
          {submitting ? t('resetPassword.submitting') : t('resetPassword.submit')}
        </button>
      </form>
    </div>
  )
}
