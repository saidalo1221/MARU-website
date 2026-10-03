import { useEffect, useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { verifyEmail } from '../api/auth'
import { useAuth } from '../context/AuthContext'
import { useLocale } from '../context/LocaleContext'
import { errorMessage } from '../api/client'
import Seo from '../components/Seo'

export default function VerifyEmail() {
  const { t } = useLocale()
  const navigate = useNavigate()
  const { refreshUser } = useAuth()
  const [params] = useSearchParams()
  const token = params.get('token') || ''
  const [status, setStatus] = useState(token ? 'verifying' : 'missing')
  const [error, setError] = useState(null)

  useEffect(() => {
    if (!token) return
    verifyEmail(token)
      .then(async () => {
        await refreshUser()
        setStatus('done')
      })
      .catch((err) => {
        setError(errorMessage(err, t('verifyEmail.failed')))
        setStatus('failed')
      })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token])

  if (status === 'missing') {
    return (
      <div className="max-w-sm mx-auto px-4 py-12 text-center">
        <p role="alert" className="text-red-600 text-sm mb-4">{t('verifyEmail.missingToken')}</p>
        <Link to="/" className="text-brand text-sm">{t('verifyEmail.backHome')}</Link>
      </div>
    )
  }

  if (status === 'verifying') {
    return (
      <div className="max-w-sm mx-auto px-4 py-12 text-center">
        <Seo title={t('verifyEmail.title')} noindex />
        <p className="text-sm text-gray-600">{t('verifyEmail.verifying')}</p>
      </div>
    )
  }

  if (status === 'done') {
    return (
      <div className="max-w-sm mx-auto px-4 py-12 text-center">
        <h1 className="text-2xl font-bold mb-4">{t('verifyEmail.title')}</h1>
        <p className="text-sm text-gray-600 mb-4">{t('verifyEmail.success')}</p>
        <button onClick={() => navigate('/')} className="bg-brand text-white px-6 py-2.5 rounded font-medium">
          {t('verifyEmail.continue')}
        </button>
      </div>
    )
  }

  return (
    <div className="max-w-sm mx-auto px-4 py-12 text-center">
      <h1 className="text-2xl font-bold mb-4">{t('verifyEmail.title')}</h1>
      <p role="alert" className="text-sm text-red-600 mb-4">{error}</p>
      <Link to="/" className="text-brand text-sm">{t('verifyEmail.backHome')}</Link>
    </div>
  )
}
