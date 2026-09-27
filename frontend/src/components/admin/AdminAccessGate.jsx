import { useEffect, useState } from 'react'
import { adminSessionCheck } from '../../api/admin'
import { requestAdminCode, verifyAdminCode } from '../../api/auth'
import { errorMessage } from '../../api/client'
import { useAuth } from '../../context/AuthContext'
import { useLocale } from '../../context/LocaleContext'

// Gates the admin panel behind the 2-step email login (password, then a code
// emailed to that account) required by app/dependencies.py's require_role()
// for every admin-role endpoint — a plain site login alone never grants
// access, regardless of the account's role. See AdminLayout.jsx.
export default function AdminAccessGate({ children }) {
  const { user, loading: authLoading, refreshUser } = useAuth()
  const { t } = useLocale()

  const [phase, setPhase] = useState('checking') // checking | credentials | code | granted
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [code, setCode] = useState('')
  const [error, setError] = useState(null)
  const [submitting, setSubmitting] = useState(false)

  const runCheck = () => {
    adminSessionCheck()
      .then(() => setPhase('granted'))
      .catch(() => {
        setEmail((e) => e || user?.email || '')
        setPhase('credentials')
      })
  }

  useEffect(() => {
    if (authLoading) return
    if (!user || user.role === 'customer') {
      setEmail((e) => e || user?.email || '')
      setPhase('credentials')
      return
    }
    runCheck()
  }, [authLoading, user]) // eslint-disable-line react-hooks/exhaustive-deps

  const handleCredentials = async (e) => {
    e.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      await requestAdminCode(email, password)
      setPhase('code')
    } catch (err) {
      setError(errorMessage(err, t('admin.login.invalidCredentials')))
    } finally {
      setSubmitting(false)
    }
  }

  const handleCode = async (e) => {
    e.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      await verifyAdminCode(email, code)
      await refreshUser()
      runCheck()
    } catch (err) {
      setError(errorMessage(err, t('admin.login.invalidCode')))
    } finally {
      setSubmitting(false)
    }
  }

  if (phase === 'checking') return null

  if (phase === 'granted') return children

  return (
    <div className="max-w-sm mx-auto px-4 py-16">
      <h1 className="text-xl font-bold mb-1">{t('admin.login.title')}</h1>
      <p className="text-sm text-gray-500 mb-6">
        {phase === 'credentials' ? t('admin.login.subtitle') : t('admin.login.codeSentTo', { email })}
      </p>

      {phase === 'credentials' && (
        <form onSubmit={handleCredentials} className="space-y-3">
          <input
            required
            type="email"
            placeholder={t('admin.login.emailPlaceholder')}
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full border border-gray-300 rounded px-3 py-2 text-sm"
          />
          <input
            required
            type="password"
            placeholder={t('admin.login.passwordPlaceholder')}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full border border-gray-300 rounded px-3 py-2 text-sm"
          />
          {error && <p className="text-sm text-red-600">{error}</p>}
          <button
            type="submit"
            disabled={submitting}
            className="w-full bg-brand text-white px-4 py-2 rounded text-sm font-medium disabled:opacity-40"
          >
            {submitting ? t('admin.common.saving') : t('admin.login.sendCode')}
          </button>
        </form>
      )}

      {phase === 'code' && (
        <form onSubmit={handleCode} className="space-y-3">
          <input
            required
            inputMode="numeric"
            pattern="[0-9]*"
            placeholder={t('admin.login.codePlaceholder')}
            value={code}
            onChange={(e) => setCode(e.target.value)}
            className="w-full border border-gray-300 rounded px-3 py-2 text-sm tracking-widest text-center text-lg"
          />
          {error && <p className="text-sm text-red-600">{error}</p>}
          <button
            type="submit"
            disabled={submitting}
            className="w-full bg-brand text-white px-4 py-2 rounded text-sm font-medium disabled:opacity-40"
          >
            {submitting ? t('admin.common.saving') : t('admin.login.verifyCode')}
          </button>
          <button
            type="button"
            onClick={() => { setPhase('credentials'); setCode(''); setError(null) }}
            className="w-full text-xs text-gray-500"
          >
            {t('admin.login.back')}
          </button>
        </form>
      )}
    </div>
  )
}
