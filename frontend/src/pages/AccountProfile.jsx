import { useEffect, useState } from 'react'
import { Navigate } from 'react-router-dom'
import { changePassword, updateProfile } from '../api/auth'
import { errorMessage } from '../api/client'
import PasswordInput from '../components/PasswordInput'
import Seo from '../components/Seo'
import Button from '../components/ui/Button'
import FormField from '../components/ui/FormField'
import { useAuth } from '../context/AuthContext'
import { useLocale } from '../context/LocaleContext'

const inputClass = 'w-full rounded-2xl border border-gray-300 bg-white px-4 py-2.5 text-sm'

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
    <div className="max-w-3xl">
      <Seo title={t('profile.title')} noindex />
      <h1 className="mb-6 text-3xl font-semibold tracking-tight md:text-4xl">{t('profile.title')}</h1>

      <form onSubmit={save} className="mb-8 grid gap-4 rounded-3xl border border-gray-200 bg-gray-50 p-6 sm:grid-cols-2">
        <h2 className="text-lg font-semibold sm:col-span-2">{t('profile.personal')}</h2>
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

      <form onSubmit={submitPassword} className="grid max-w-md gap-4 rounded-3xl border border-gray-200 bg-gray-50 p-6">
        <h2 className="text-lg font-semibold">{t('profile.passwordTitle')}</h2>
        <PasswordInput required autoComplete="current-password" placeholder={t('profile.currentPassword')} aria-label={t('profile.currentPassword')} value={pw.current} onChange={(e) => setPw((p) => ({ ...p, current: e.target.value }))} className={inputClass} />
        <PasswordInput required autoComplete="new-password" placeholder={t('profile.newPassword')} aria-label={t('profile.newPassword')} value={pw.next} onChange={(e) => setPw((p) => ({ ...p, next: e.target.value }))} className={inputClass} />
        <PasswordInput required autoComplete="new-password" placeholder={t('profile.confirmPassword')} aria-label={t('profile.confirmPassword')} value={pw.repeat} onChange={(e) => setPw((p) => ({ ...p, repeat: e.target.value }))} className={inputClass} />
        <p className="text-xs text-gray-500">{t('profile.passwordHint')}</p>
        {pwError && <p role="alert" className="text-sm text-red-600">{pwError}</p>}
        {pwDone && <p role="status" className="text-sm text-green-700">{t('profile.passwordChanged')}</p>}
        <div>
          <button type="submit" disabled={pwBusy} className="rounded-full border border-gray-300 px-5 py-2 text-sm font-medium transition-colors hover:bg-brand-light disabled:opacity-40">
            {t('profile.changePassword')}
          </button>
        </div>
      </form>
    </div>
  )
}
