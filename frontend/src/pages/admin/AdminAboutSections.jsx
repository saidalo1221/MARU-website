import { useEffect, useState } from 'react'
import {
  adminCreateAboutSection,
  adminDeleteAboutSection,
  adminListAboutSectionTranslations,
  adminListAboutSections,
  adminMoveAboutSection,
  adminUpdateAboutSection,
  adminUpsertAboutSectionTranslation,
} from '../../api/admin'
import { errorMessage } from '../../api/client'
import { useLocale } from '../../context/LocaleContext'

const TRANSLATION_LOCALES = ['ru', 'uz', 'en']
const emptyTranslation = { title: '', body: '' }

function SectionTranslations({ sectionId }) {
  const { t } = useLocale()
  const [activeLocale, setActiveLocale] = useState('ru')
  const [translations, setTranslations] = useState({})
  const [form, setForm] = useState(emptyTranslation)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    adminListAboutSectionTranslations(sectionId)
      .then((rows) => setTranslations(Object.fromEntries(rows.map((row) => [row.locale, row]))))
      .catch((err) => setError(errorMessage(err, t('admin.aboutSections.loadFailed'))))
      .finally(() => setLoading(false))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sectionId])

  useEffect(() => {
    const existing = translations[activeLocale]
    setForm(existing ? { title: existing.title, body: existing.body } : emptyTranslation)
    setError(null)
  }, [activeLocale, translations])

  const update = (field) => (e) => setForm((f) => ({ ...f, [field]: e.target.value }))

  const save = async (e) => {
    e.preventDefault()
    setError(null)
    setSaving(true)
    try {
      const saved = await adminUpsertAboutSectionTranslation(sectionId, activeLocale, form)
      setTranslations((t2) => ({ ...t2, [activeLocale]: saved }))
    } catch (err) {
      setError(errorMessage(err, t('admin.aboutSections.saveFailed')))
    } finally {
      setSaving(false)
    }
  }

  if (loading) return <p className="text-xs text-gray-400">{t('admin.common.loading')}</p>

  return (
    <div className="mt-3 pt-3 border-t border-gray-100">
      <div className="flex gap-2 mb-2">
        {TRANSLATION_LOCALES.map((loc) => (
          <button
            key={loc}
            type="button"
            onClick={() => setActiveLocale(loc)}
            className={`px-2 py-1 rounded text-xs border ${activeLocale === loc ? 'bg-brand text-white border-brand' : 'border-gray-300'}`}
          >
            {loc.toUpperCase()}
          </button>
        ))}
      </div>
      <form onSubmit={save} className="space-y-2">
        <input required placeholder={t('admin.common.name')} aria-label={t('admin.common.name')} value={form.title} onChange={update('title')} className="w-full border border-gray-300 rounded px-2 py-1.5 text-sm" />
        <textarea required placeholder={t('admin.aboutSections.body')} aria-label={t('admin.aboutSections.body')} value={form.body} onChange={update('body')} rows={3} className="w-full border border-gray-300 rounded px-2 py-1.5 text-sm" />
        {error && <p role="alert" className="text-xs text-red-600">{error}</p>}
        <button type="submit" disabled={saving} className="bg-brand text-white px-3 py-1.5 rounded text-xs disabled:opacity-40">
          {saving ? t('admin.common.saving') : t('admin.common.save')}
        </button>
      </form>
    </div>
  )
}

function SectionBlock({ section, isFirst, isLast, onChanged }) {
  const { t } = useLocale()
  const [expanded, setExpanded] = useState(false)
  const [form, setForm] = useState({ title: section.title, body: section.body })
  const [error, setError] = useState(null)
  const [saving, setSaving] = useState(false)

  const update = (field) => (e) => setForm((f) => ({ ...f, [field]: e.target.value }))

  const save = async (e) => {
    e.preventDefault()
    setError(null)
    setSaving(true)
    try {
      await adminUpdateAboutSection(section.id, form)
      await onChanged()
    } catch (err) {
      setError(errorMessage(err, t('admin.aboutSections.saveFailed')))
    } finally {
      setSaving(false)
    }
  }

  const move = async (direction) => {
    try {
      await adminMoveAboutSection(section.id, direction)
      await onChanged()
    } catch (err) {
      setError(errorMessage(err, t('admin.aboutSections.saveFailed')))
    }
  }

  const remove = async () => {
    try {
      await adminDeleteAboutSection(section.id)
      await onChanged()
    } catch (err) {
      setError(errorMessage(err, t('admin.aboutSections.deleteFailed')))
    }
  }

  return (
    <div className="border border-gray-200 rounded-lg p-4 mb-3">
      <div className="flex items-center justify-between">
        <button onClick={() => setExpanded((x) => !x)} className="font-medium text-left flex-1">
          {section.display_title}
          {section.display_title !== section.title && (
            <span className="text-gray-400 font-normal"> ({section.title})</span>
          )}
        </button>
        <div className="flex items-center gap-2 text-sm">
          <button type="button" onClick={() => move('up')} disabled={isFirst} className="text-gray-500 disabled:opacity-30">&uarr;</button>
          <button type="button" onClick={() => move('down')} disabled={isLast} className="text-gray-500 disabled:opacity-30">&darr;</button>
          <button type="button" onClick={remove} className="text-red-600">{t('admin.common.delete')}</button>
        </div>
      </div>

      {expanded && (
        <>
          <form onSubmit={save} className="space-y-2 mt-3">
            <input required placeholder={t('admin.common.name')} aria-label={t('admin.common.name')} value={form.title} onChange={update('title')} className="w-full border border-gray-300 rounded px-2 py-1.5 text-sm" />
            <textarea required placeholder={t('admin.aboutSections.body')} aria-label={t('admin.aboutSections.body')} value={form.body} onChange={update('body')} rows={3} className="w-full border border-gray-300 rounded px-2 py-1.5 text-sm" />
            {error && <p role="alert" className="text-xs text-red-600">{error}</p>}
            <button type="submit" disabled={saving} className="bg-brand text-white px-3 py-1.5 rounded text-xs disabled:opacity-40">
              {saving ? t('admin.common.saving') : t('admin.common.save')}
            </button>
          </form>
          <SectionTranslations sectionId={section.id} />
        </>
      )}
    </div>
  )
}

export default function AdminAboutSections() {
  const { t, locale } = useLocale()
  const [sections, setSections] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [form, setForm] = useState({ title: '', body: '' })
  const [formOpen, setFormOpen] = useState(false)
  const [formError, setFormError] = useState(null)
  const [submitting, setSubmitting] = useState(false)

  const load = () =>
    adminListAboutSections(locale)
      .then(setSections)
      .catch((err) => setError(errorMessage(err, t('admin.aboutSections.loadFailed'))))
      .finally(() => setLoading(false))

  useEffect(() => { load() }, [locale]) // eslint-disable-line react-hooks/exhaustive-deps

  const handleAdd = async (e) => {
    e.preventDefault()
    setFormError(null)
    setSubmitting(true)
    try {
      await adminCreateAboutSection(form)
      setForm({ title: '', body: '' })
      setFormOpen(false)
      await load()
    } catch (err) {
      setFormError(errorMessage(err, t('admin.aboutSections.saveFailed')))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-1">
        <h1 className="text-2xl font-bold">{t('admin.aboutSections.title')}</h1>
        {!formOpen && <button onClick={() => setFormOpen(true)} className="bg-brand text-white px-4 py-2 rounded text-sm font-medium">{t('admin.aboutSections.add')}</button>}
      </div>
      <p className="text-sm text-gray-500 mb-4">{t('admin.aboutSections.subtitle')}</p>

      {formOpen && (
        <form onSubmit={handleAdd} className="border border-gray-200 rounded-lg p-4 mb-6 space-y-3">
          <input required placeholder={t('admin.common.name')} aria-label={t('admin.common.name')} value={form.title} onChange={(e) => setForm((f) => ({ ...f, title: e.target.value }))} className="w-full border border-gray-300 rounded px-3 py-2 text-sm" />
          <textarea required placeholder={t('admin.aboutSections.body')} aria-label={t('admin.aboutSections.body')} value={form.body} onChange={(e) => setForm((f) => ({ ...f, body: e.target.value }))} rows={3} className="w-full border border-gray-300 rounded px-3 py-2 text-sm" />
          {formError && <p role="alert" className="text-sm text-red-600">{formError}</p>}
          <div className="flex gap-2">
            <button type="submit" disabled={submitting} className="bg-brand text-white px-4 py-2 rounded text-sm font-medium disabled:opacity-40">
              {submitting ? t('admin.common.saving') : t('admin.common.save')}
            </button>
            <button type="button" onClick={() => setFormOpen(false)} className="border border-gray-300 rounded px-4 py-2 text-sm">{t('admin.common.cancel')}</button>
          </div>
        </form>
      )}

      {loading && <p>{t('admin.common.loading')}</p>}
      {error && <p role="alert" className="text-red-600 text-sm">{error}</p>}

      {!loading && !error && sections.map((s, i) => (
        <SectionBlock key={s.id} section={s} isFirst={i === 0} isLast={i === sections.length - 1} onChanged={load} />
      ))}
      {!loading && !error && sections.length === 0 && <p className="text-gray-400 text-sm">{t('admin.aboutSections.none')}</p>}
    </div>
  )
}
