import { useState } from 'react'
import { useLocation } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import { useLocale } from '../../context/LocaleContext'
import { resendVerification } from '../../api/auth'
import { errorMessage } from '../../api/client'

export default function EmailVerifyBanner() {
  const { t } = useLocale()
  const { user } = useAuth()
  const location = useLocation()
  const [state, setState] = useState('idle') // idle | sending | sent | failed
  const [error, setError] = useState(null)

  if (!user || user.email_verified || location.pathname === '/verify-email') return null

  const handleResend = async () => {
    setState('sending')
    setError(null)
    try {
      await resendVerification()
      setState('sent')
    } catch (err) {
      setError(errorMessage(err, t('verifyEmail.resendFailed')))
      setState('failed')
    }
  }

  return (
    <div className="bg-amber-50 border-b border-amber-200 text-amber-800 text-sm px-4 py-2 flex flex-wrap items-center justify-center gap-2 text-center">
      <span>{t('verifyEmail.banner')}</span>
      {state === 'sent' ? (
        <span className="font-medium">{t('verifyEmail.resendSent')}</span>
      ) : (
        <button
          onClick={handleResend}
          disabled={state === 'sending'}
          className="underline font-medium disabled:opacity-50"
        >
          {state === 'sending' ? t('verifyEmail.resending') : t('verifyEmail.resend')}
        </button>
      )}
      {error && <span className="text-red-600">{error}</span>}
    </div>
  )
}
