import { useState } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { useLocale } from '../context/LocaleContext'
import { errorMessage } from '../api/client'
import { eraseMyAccount, exportMyData } from '../api/privacy'
import AccountNav from '../components/account/AccountNav'
import PasswordInput from '../components/PasswordInput'
import Seo from '../components/Seo'

export default function AccountPrivacy() {
  const { t } = useLocale()
  const { user, loading: authLoading, logout } = useAuth()
  const navigate = useNavigate()
  const [exportError, setExportError] = useState(null)
  const [password, setPassword] = useState('')
  const [eraseError, setEraseError] = useState(null)
  const [understood, setUnderstood] = useState(false)
  const [busy, setBusy] = useState(false)

  if (authLoading) return null
  if (!user) return <Navigate to="/login" replace />

  const download = async () => {
    setExportError(null)
    try {
      const data = await exportMyData()
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'maru-my-data.json'
      a.click()
      URL.revokeObjectURL(url)
    } catch (err) {
      setExportError(errorMessage(err, t('privacy.exportFailed')))
    }
  }

  const erase = async (e) => {
    e.preventDefault()
    setEraseError(null)
    setBusy(true)
    try {
      await eraseMyAccount(password)
      logout()
      navigate('/', { replace: true })
    } catch (err) {
      setEraseError(errorMessage(err, t('privacy.eraseFailed')))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="max-w-3xl mx-auto px-4 py-8">
      <Seo title={t('privacy.title')} noindex />
      <AccountNav />
      <h1 className="text-2xl font-bold mb-6">{t('privacy.title')}</h1>

      <section className="mb-8">
        <h2 className="font-semibold mb-1">{t('privacy.exportTitle')}</h2>
        <p className="text-sm text-gray-500 mb-3">{t('privacy.exportText')}</p>
        <button onClick={download} className="border border-brand text-brand rounded px-4 py-2 text-sm">{t('privacy.exportButton')}</button>
        {exportError && <p role="alert" className="text-sm text-red-600 mt-2">{exportError}</p>}
      </section>

      <section>
        <h2 className="font-semibold mb-1 text-red-600">{t('privacy.eraseTitle')}</h2>
        <p className="text-sm text-gray-500 mb-3">{t('privacy.eraseText')}</p>
        <form onSubmit={erase} className="max-w-sm space-y-2">
          <PasswordInput
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder={t('privacy.password')}
            aria-label={t('privacy.password')}
            required
            autoComplete="current-password"
            className="w-full border border-gray-300 rounded px-3 py-2 text-sm"
          />
          <label className="flex items-start gap-2 text-sm">
            <input type="checkbox" checked={understood} onChange={(e) => setUnderstood(e.target.checked)} className="mt-1" />
            <span>{t('privacy.understand')}</span>
          </label>
          {eraseError && <p role="alert" className="text-sm text-red-600">{eraseError}</p>}
          <button type="submit" disabled={busy || !password || !understood} className="border border-red-400 text-red-600 rounded px-4 py-2 text-sm disabled:opacity-40">
            {t('privacy.eraseButton')}
          </button>
        </form>
      </section>
    </div>
  )
}
