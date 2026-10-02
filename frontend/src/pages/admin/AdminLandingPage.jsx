import { useEffect, useState } from 'react'
import { adminListContentOverrides, adminSaveContentOverrides } from '../../api/siteContent'
import { errorMessage } from '../../api/client'
import { translations } from '../../i18n/translations'
import { useLocale } from '../../context/LocaleContext'

const LOCALES = ['ru', 'uz', 'en']

// Every text on the landing page that comes from the translation files, in page order.
// The FAQ questions, reviews and products on the page are edited in their own admin sections.
const GROUPS = [
  ['gTop', ['heroTag', 'title', 'subtitle', 'cta', 'ctaBusiness']],
  ['gSizes', ['sizesTitle']],
  ['gBest', ['bestSellers']],
  ['gWhy', ['whyTitle', 'benefitMaterial', 'benefitMaterialText', 'benefitOwn', 'benefitOwnText', 'benefitRange', 'benefitRangeText', 'benefitQuality', 'benefitQualityText', 'benefitB2b', 'benefitB2bText', 'benefitExport', 'benefitExportText']],
  ['gSets', ['setsTitle', 'setsText', 'pack', 'packText']],
  ['gB2b', ['b2bTitle', 'b2bText', 'b2bCta']],
  ['gManufacturing', ['manufacturingTitle', 'manufacturingText', 'statSizes', 'statRange', 'learnMore']],
  ['gReviews', ['reviewsTitle', 'faqTitle', 'allQuestions']],
  ['gFinal', ['finalTitle', 'finalCta']],
]

export default function AdminLandingPage() {
  const { t } = useLocale()
  const [locale, setLocale] = useState('ru')
  const [saved, setSaved] = useState({}) // "locale|key" -> saved override
  const [draft, setDraft] = useState({}) // "locale|key" -> text being typed
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [saving, setSaving] = useState(false)
  const [done, setDone] = useState(false)

  const load = () =>
    adminListContentOverrides()
      .then((rows) => {
        const map = Object.fromEntries(rows.map((r) => [`${r.locale}|${r.key}`, r.value]))
        setSaved(map)
        setDraft(map)
      })
      .catch((err) => setError(errorMessage(err, t('adminContent.landingLoadFailed'))))
      .finally(() => setLoading(false))

  useEffect(() => { load() }, [])

  const known = new Set(GROUPS.flatMap(([, keys]) => keys))
  const extra = Object.keys(translations.en.home).filter((k) => !known.has(k))
  const groups = extra.length ? [...GROUPS, ['gOther', extra]] : GROUPS

  const changed = Object.keys({ ...saved, ...draft }).filter((id) => id.startsWith(`${locale}|`) && (draft[id] || '') !== (saved[id] || ''))

  const save = async () => {
    setSaving(true)
    setError(null)
    setDone(false)
    try {
      await adminSaveContentOverrides(changed.map((id) => ({ key: id.split('|')[1], locale, value: draft[id] || '' })))
      await load()
      setDone(true)
    } catch (err) {
      setError(errorMessage(err, t('adminContent.landingSaveFailed')))
    } finally {
      setSaving(false)
    }
  }

  if (loading) return <p className="text-sm text-gray-500">{t('adminContent.loading')}</p>

  return (
    <div className="max-w-3xl">
      <h1 className="mb-1 text-2xl font-bold">{t('adminContent.landingTitle')}</h1>
      <p className="mb-4 text-sm text-gray-600">{t('adminContent.landingIntro', { n: '{n}' })}</p>

      <div className="mb-4 flex flex-wrap items-center gap-2">
        {LOCALES.map((loc) => (
          <button
            key={loc}
            type="button"
            onClick={() => { setLocale(loc); setDone(false) }}
            className={`rounded px-3 py-1.5 text-sm border ${locale === loc ? 'bg-brand text-white border-brand' : 'border-gray-300'}`}
          >
            {loc.toUpperCase()}
          </button>
        ))}
        <span className="text-xs text-gray-500">{changed.length ? t('adminContent.unsaved', { n: changed.length }) : t('adminContent.noUnsaved')}</span>
      </div>

      {groups.map(([name, keys]) => (
        <fieldset key={name} className="mb-5 rounded-lg border border-gray-200 p-4">
          <legend className="px-2 text-sm font-semibold">{t(`adminContent.${name}`)}</legend>
          <div className="space-y-3">
            {keys.map((key) => {
              const id = `${locale}|${key}`
              const builtIn = translations[locale]?.home?.[key] ?? translations.en.home[key]
              const long = String(builtIn).length > 70
              const Field = long ? 'textarea' : 'input'
              return (
                <label key={key} className="block">
                  <span className="mb-1 block text-xs text-gray-500">{key}</span>
                  <Field
                    value={draft[id] || ''}
                    placeholder={builtIn}
                    rows={long ? 3 : undefined}
                    maxLength={5000}
                    onChange={(e) => { setDraft((d) => ({ ...d, [id]: e.target.value })); setDone(false) }}
                    className="w-full rounded border border-gray-300 px-3 py-2 text-sm"
                  />
                </label>
              )
            })}
          </div>
        </fieldset>
      ))}

      {error && <p role="alert" className="mb-2 text-sm text-red-600">{error}</p>}
      {done && <p role="status" className="mb-2 text-sm text-green-700">{t('adminContent.landingSaved')}</p>}
      <div className="sticky bottom-0 -mx-1 bg-white/90 px-1 py-3 backdrop-blur">
        <button type="button" onClick={save} disabled={saving || !changed.length} className="rounded bg-brand px-4 py-2 text-sm font-medium text-white disabled:opacity-40">
          {saving ? t('adminContent.saving') : t('adminContent.saveTexts', { lang: locale.toUpperCase() })}
        </button>
      </div>
    </div>
  )
}
