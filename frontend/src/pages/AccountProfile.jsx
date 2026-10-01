import { useEffect, useState } from 'react'
import { Navigate } from 'react-router-dom'
import { changePassword, updateProfile } from '../api/auth'
import { errorMessage } from '../api/client'
import AccountNav from '../components/account/AccountNav'
import PasswordInput from '../components/PasswordInput'
import Seo from '../components/Seo'
import Button from '../components/ui/Button'
import FormField from '../components/ui/FormField'
import { useAuth } from '../context/AuthContext'
import { useLocale } from '../context/LocaleContext'

const inputClass = 'w-full border border-gray-300 rounded px-3 py-2 text-sm'

export default function AccountProfile() {
  const { t } = useLocale()
  const { user, loading: authLoading, refreshUser } = useAuth()
  const [form, setForm] = useState({ first_name: '', last_name: '', phone: '' })
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)
  const [error, setError] = useState(null)
  const [pw, setPw] = useState({ current: '', next: '', repeat: '' })
  const [pwBusy, setPwBusy] = useState(false)
  const [pwDone, setPwDone] = useState(false)
  const [pwError, setPwError] = useState(null)

  useEffect(() => {
    if (user) setForm({ first_name: user.first_name || '', last_name: user.last_name || '', phone: user.phone || '' })
  }, [user])

  if (authLoading) return null
  if (!user) return <Navigate to="/login" replace />

  const update = (field) => (e) => {
    setSaved(false)
    setForm((f) => ({ ...f, [field]: e.target.value }))
  }

  const save = async (e) => {
    e.preventDefault()
    setError(null)
    setSaving(true)
    try {
      await updateProfile(form)
      await refreshUser()
      setSaved(true)
    } catch (err) {
      setError(errorMessage(err, t('profile.saveFailed')))
    } finally {
      setSaving(false)
    }
  }

  const submitPassword = async (e) => {
    e.preventDefault()
    setPwError(null)
    setPwDone(false)
    if (pw.next !== pw.repeat) {
      setPwError(t('profile.mismatch'))
      return
    }
    setPwBusy(true)
    try {
      await changePassword(pw.current, pw.next)
      setPw({ current: '', next: '', repeat: '' })
      setPwDone(true)
    } catch (err) {
      setPwError(errorMessage(err, t('profile.passwordFailed')))
    } finally {
      setPwBusy(false)
    }
  }

  return (
    <div className="max-w-3xl mx-auto px-4 py-8">
      <Seo title={t('profile.title')} noindex />
      <AccountNav />
      <h1 className="text-2xl font-bold mb-6">{t('profile.title')}</h1>

      <form onSubmit={save} className="border border-gray-200 rounded-lg p-4 mb-8 grid sm:grid-cols-2 gap-3">
        <h2 className="font-semibold sm:col-span-2">{t('profile.personal')}</h2>
        <FormField label={t('profile.firstName')} value={form.first_name} onChange={update('first_name')} autoComplete="given-name" />
        <FormField label={t('profile.lastName')} value={form.last_name} onChange={update('last_name')} autoComplete="family-name" />
        <FormField label={t('profile.phone')} helper={t('profile.phoneHint')} value={form.phone} onChange={update('phone')} type="tel" autoComplete="tel" />
        <FormField label={t('profile.email')} value={user.email} disabled />
        {error && <p role="alert" className="text-sm text-red-600 sm:col-span-2">{error}</p>}
        {saved && <p role="status" className="text-sm text-green-700 sm:col-span-2">{t('profile.saved')}</p>}
        <div className="sm:col-span-2">
          <Button type="submit" loading={saving} loadingLabel={t('profile.saving')}>{t('profile.save')}</Button>
        </div>
      </form>

      <form onSubmit={submitPassword} className="border border-gray-200 rounded-lg p-4 grid gap-3 max-w-md">
        <h2 className="font-semibold">{t('profile.passwordTitle')}</h2>
        <PasswordInput required autoComplete="current-password" placeholder={t('profile.currentPassword')} aria-label={t('profile.currentPassword')} value={pw.current} onChange={(e) => setPw((p) => ({ ...p, current: e.target.value }))} className={inputClass} />
        <PasswordInput required autoComplete="new-password" placeholder={t('profile.newPassword')} aria-label={t('profile.newPassword')} value={pw.next} onChange={(e) => setPw((p) => ({ ...p, next: e.target.value }))} className={inputClass} />
        <PasswordInput required autoComplete="new-password" placeholder={t('profile.confirmPassword')} aria-label={t('profile.confirmPassword')} value={pw.repeat} onChange={(e) => setPw((p) => ({ ...p, repeat: e.target.value }))} className={inputClass} />
        <p className="text-xs text-gray-500">{t('profile.passwordHint')}</p>
        {pwError && <p role="alert" className="text-sm text-red-600">{pwError}</p>}
        {pwDone && <p role="status" className="text-sm text-green-700">{t('profile.passwordChanged')}</p>}
        <div>
          <button type="submit" disabled={pwBusy} className="border border-gray-300 px-4 py-2 rounded text-sm font-medium disabled:opacity-40">
            {t('profile.changePassword')}
          </button>
        </div>
      </form>
    </div>
  )
}
