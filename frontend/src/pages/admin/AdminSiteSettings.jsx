import { useEffect, useState } from 'react'
import {
  adminGetSiteSettings,
  adminListSiteSettingsTranslations,
  adminUpdateSiteSettings,
  adminUpsertSiteSettingsTranslation,
} from '../../api/admin'
import { errorMessage } from '../../api/client'
import { useLocale } from '../../context/LocaleContext'
import MapPicker from '../../components/MapPicker'

const LOCALES = ['ru', 'uz', 'en']
const emptyTranslation = { address: '', about_title: '', about_body: '' }

export default function AdminSiteSettings() {
  const { t } = useLocale()

  const [form, setForm] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [saving, setSaving] = useState(false)
  const [saveError, setSaveError] = useState(null)

  const [activeLocale, setActiveLocale] = useState('ru')
  const [translations, setTranslations] = useState({})
  const [translationForm, setTranslationForm] = useState(emptyTranslation)
  const [translationSaving, setTranslationSaving] = useState(false)
  const [translationError, setTranslationError] = useState(null)

  const load = () =>
    Promise.all([adminGetSiteSettings(), adminListSiteSettingsTranslations()])
      .then(([s, tr]) => {
        setForm({
          phone: s.phone || '',
          email: s.email || '',
          address: s.address || '',
          latitude: s.latitude,
          longitude: s.longitude,
          about_title: s.about_title || '',
          about_body: s.about_body || '',
          facebook_url: s.facebook_url || '',
          instagram_url: s.instagram_url || '',
          telegram_url: s.telegram_url || '',
          youtube_url: s.youtube_url || '',
        })
        setTranslations(Object.fromEntries(tr.map((row) => [row.locale, row])))
      })
      .catch((err) => setError(errorMessage(err, t('admin.siteSettings.loadFailed'))))
      .finally(() => setLoading(false))

  useEffect(() => { load() }, []) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    const existing = translations[activeLocale]
    setTranslationForm(
      existing
        ? { address: existing.address || '', about_title: existing.about_title || '', about_body: existing.about_body || '' }
        : emptyTranslation
    )
    setTranslationError(null)
  }, [activeLocale, translations])

  if (loading) return <p>{t('admin.common.loading')}</p>
  if (error) return <p role="alert" className="text-red-600 text-sm">{error}</p>
  if (!form) return null

  const update = (field) => (e) => setForm((f) => ({ ...f, [field]: e.target.value }))

  const handleSave = async (e) => {
    e.preventDefault()
    setSaveError(null)
    setSaving(true)
    try {
      const updated = await adminUpdateSiteSettings({
        ...form,
        latitude: form.latitude === '' || form.latitude == null ? null : Number(form.latitude),
        longitude: form.longitude === '' || form.longitude == null ? null : Number(form.longitude),
      })
      setForm({ ...updated })
    } catch (err) {
      setSaveError(errorMessage(err, t('admin.siteSettings.saveFailed')))
    } finally {
      setSaving(false)
    }
  }

  const updateTranslation = (field) => (e) => setTranslationForm((f) => ({ ...f, [field]: e.target.value }))

  const handleTranslationSave = async (e) => {
    e.preventDefault()
    setTranslationError(null)
    setTranslationSaving(true)
    try {
      const saved = await adminUpsertSiteSettingsTranslation(activeLocale, translationForm)
      setTranslations((t2) => ({ ...t2, [activeLocale]: saved }))
    } catch (err) {
      setTranslationError(errorMessage(err, t('admin.siteSettings.saveFailed')))
    } finally {
      setTranslationSaving(false)
    }
  }

  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">{t('admin.siteSettings.title')}</h1>

      <form onSubmit={handleSave} className="border border-gray-200 rounded-lg p-4 mb-8 grid grid-cols-2 gap-3">
        <input placeholder={t('admin.siteSettings.phone')} aria-label={t('admin.siteSettings.phone')} value={form.phone} onChange={update('phone')} className="border border-gray-300 rounded px-3 py-2 text-sm" />
        <input placeholder={t('admin.siteSettings.email')} aria-label={t('admin.siteSettings.email')} value={form.email} onChange={update('email')} className="border border-gray-300 rounded px-3 py-2 text-sm" />
        <input placeholder={t('admin.siteSettings.address')} aria-label={t('admin.siteSettings.address')} value={form.address} onChange={update('address')} className="border border-gray-300 rounded px-3 py-2 text-sm col-span-2" />

        <div className="col-span-2">
          <label className="block text-xs text-gray-500 mb-1">{t('admin.siteSettings.mapHint')}</label>
          <MapPicker
            latitude={form.latitude}
            longitude={form.longitude}
            onChange={({ latitude, longitude }) => setForm((f) => ({ ...f, latitude, longitude }))}
          />
        </div>

        {['facebook_url', 'instagram_url', 'telegram_url', 'youtube_url'].map((field) => (
          <input key={field} type="url" placeholder={t(`admin.siteSettings.${field}`)} aria-label={t(`admin.siteSettings.${field}`)} value={form[field]} onChange={update(field)} className="border border-gray-300 rounded px-3 py-2 text-sm" />
        ))}

        <input placeholder={t('admin.siteSettings.aboutTitle')} aria-label={t('admin.siteSettings.aboutTitle')} value={form.about_title} onChange={update('about_title')} className="border border-gray-300 rounded px-3 py-2 text-sm col-span-2" />
        <textarea placeholder={t('admin.siteSettings.aboutBody')} aria-label={t('admin.siteSettings.aboutBody')} value={form.about_body} onChange={update('about_body')} rows={6} className="border border-gray-300 rounded px-3 py-2 text-sm col-span-2" />

        {saveError && <p role="alert" className="text-sm text-red-600 col-span-2">{saveError}</p>}
        <div className="col-span-2">
          <button type="submit" disabled={saving} className="bg-brand text-white px-4 py-2 rounded text-sm font-medium disabled:opacity-40">
            {saving ? t('admin.common.saving') : t('admin.common.save')}
          </button>
        </div>
      </form>

      <h2 className="text-lg font-bold mb-3">{t('admin.blog.translations')}</h2>
      <div className="flex gap-2 mb-4">
        {LOCALES.map((loc) => (
          <button
            key={loc}
            onClick={() => setActiveLocale(loc)}
            className={`px-3 py-1.5 rounded text-sm border ${activeLocale === loc ? 'bg-brand text-white border-brand' : 'border-gray-300'}`}
          >
            {loc.toUpperCase()}
          </button>
        ))}
      </div>
      <form onSubmit={handleTranslationSave} className="border border-gray-200 rounded-lg p-4 space-y-3">
        <input placeholder={t('admin.siteSettings.address')} aria-label={t('admin.siteSettings.address')} value={translationForm.address} onChange={updateTranslation('address')} className="w-full border border-gray-300 rounded px-3 py-2 text-sm" />
        <input placeholder={t('admin.siteSettings.aboutTitle')} aria-label={t('admin.siteSettings.aboutTitle')} value={translationForm.about_title} onChange={updateTranslation('about_title')} className="w-full border border-gray-300 rounded px-3 py-2 text-sm" />
        <textarea placeholder={t('admin.siteSettings.aboutBody')} aria-label={t('admin.siteSettings.aboutBody')} value={translationForm.about_body} onChange={updateTranslation('about_body')} rows={6} className="w-full border border-gray-300 rounded px-3 py-2 text-sm" />
        {translationError && <p role="alert" className="text-sm text-red-600">{translationError}</p>}
        <button type="submit" disabled={translationSaving} className="bg-brand text-white px-4 py-2 rounded text-sm font-medium disabled:opacity-40">
          {translationSaving ? t('admin.common.saving') : t('admin.common.save')}
        </button>
      </form>
    </div>
  )
}
