import { useEffect, useState } from 'react'
import { adminListSeoMeta, adminSaveSeoMeta } from '../../api/siteContent'
import { errorMessage } from '../../api/client'
import { useLocale } from '../../context/LocaleContext'

const LOCALES = ['ru', 'uz', 'en']
const PAGES = [
  ['/', 'pHome'], ['/shop', 'pShop'], ['/blog', 'pBlog'], ['/about', 'pAbout'], ['/manufacturing', 'pManufacturing'],
  ['/quality', 'pQuality'], ['/wholesale', 'pWholesale'], ['/b2b', 'pB2b'], ['/distributor', 'pDistributor'],
  ['/quote', 'pQuote'], ['/contact', 'pContact'], ['/delivery', 'pDelivery'], ['/payment', 'pPayment'],
  ['/returns', 'pReturns'], ['/faq', 'pFaq'], ['/privacy', 'pPrivacy'], ['/terms', 'pTerms'],
]
const empty = { title: '', description: '', image_url: '', noindex: false }

export default function AdminSeo() {
  const { t } = useLocale()
  const [rows, setRows] = useState([])
  const [path, setPath] = useState('/')
  const [custom, setCustom] = useState('')
  const [locale, setLocale] = useState('ru')
  const [form, setForm] = useState(empty)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [saving, setSaving] = useState(false)
  const [done, setDone] = useState(false)

  const load = () =>
    adminListSeoMeta()
      .then(setRows)
      .catch((err) => setError(errorMessage(err, t('adminContent.seoLoadFailed'))))
      .finally(() => setLoading(false))
  useEffect(() => { load() }, [])

  const activePath = custom.trim() || path
  useEffect(() => {
    const row = rows.find((r) => r.path === activePath && r.locale === locale)
    setForm(row ? { title: row.title || '', description: row.description || '', image_url: row.image_url || '', noindex: row.noindex } : empty)
    setDone(false)
  }, [rows, activePath, locale])

  const set = (field) => (e) => { setForm((f) => ({ ...f, [field]: e.target.type === 'checkbox' ? e.target.checked : e.target.value })); setDone(false) }

  const save = async (e) => {
    e.preventDefault()
    setSaving(true)
    setError(null)
    try {
      await adminSaveSeoMeta({ path: activePath, locale, ...form })
      await load()
      setDone(true)
    } catch (err) {
      setError(errorMessage(err, t('adminContent.seoSaveFailed')))
    } finally {
      setSaving(false)
    }
  }

  const has = (p) => rows.some((r) => r.path === p)
  const origin = typeof window !== 'undefined' ? window.location.origin : ''
  const previewTitle = form.title || t('adminContent.previewTitle')

  if (loading) return <p className="text-sm text-gray-500">{t('adminContent.loading')}</p>

  return (
    <div className="max-w-3xl">
      <h1 className="mb-1 text-2xl font-bold">{t('adminContent.seoTitle')}</h1>
      <p className="mb-4 text-sm text-gray-600">{t('adminContent.seoIntro')}</p>

      <div className="mb-4 grid gap-3 sm:grid-cols-2">
        <label className="block text-sm">
          <span className="mb-1 block text-xs text-gray-500">{t('adminContent.page')}</span>
          <select value={path} onChange={(e) => { setPath(e.target.value); setCustom('') }} className="w-full rounded border border-gray-300 px-3 py-2 text-sm">
            {PAGES.map(([p, name]) => <option key={p} value={p}>{t(`adminContent.${name}`)} ({p}){has(p) ? ' *' : ''}</option>)}
          </select>
        </label>
        <label className="block text-sm">
          <span className="mb-1 block text-xs text-gray-500">{t('adminContent.otherAddress')}</span>
          <input value={custom} onChange={(e) => setCustom(e.target.value)} placeholder="/" className="w-full rounded border border-gray-300 px-3 py-2 text-sm" />
        </label>
      </div>
      <div className="mb-4 flex gap-2">
        {LOCALES.map((loc) => (
          <button key={loc} type="button" onClick={() => setLocale(loc)} className={`rounded px-3 py-1.5 text-sm border ${locale === loc ? 'bg-brand text-white border-brand' : 'border-gray-300'}`}>
            {loc.toUpperCase()}
          </button>
        ))}
      </div>

      <form onSubmit={save} className="space-y-3 rounded-lg border border-gray-200 p-4">
        <label className="block">
          <span className="mb-1 flex justify-between text-xs text-gray-500"><span>{t('adminContent.titleLabel')}</span><span className={form.title.length > 60 ? 'text-red-600' : ''}>{form.title.length}/60</span></span>
          <input value={form.title} maxLength={255} onChange={set('title')} className="w-full rounded border border-gray-300 px-3 py-2 text-sm" />
        </label>
        <label className="block">
          <span className="mb-1 flex justify-between text-xs text-gray-500"><span>{t('adminContent.descLabel')}</span><span className={form.description.length > 160 ? 'text-red-600' : ''}>{form.description.length}/160</span></span>
          <textarea value={form.description} maxLength={500} rows={3} onChange={set('description')} className="w-full rounded border border-gray-300 px-3 py-2 text-sm" />
        </label>
        <label className="block">
          <span className="mb-1 block text-xs text-gray-500">{t('adminContent.imageLabel')}</span>
          <input type="url" value={form.image_url} maxLength={500} onChange={set('image_url')} placeholder="https://" className="w-full rounded border border-gray-300 px-3 py-2 text-sm" />
        </label>
        <label className="flex items-center gap-2 text-sm">
          <input type="checkbox" checked={form.noindex} onChange={set('noindex')} />
          {t('adminContent.noindex')}
        </label>

        <div className="rounded border border-gray-200 bg-gray-50 p-3" aria-label={t('adminContent.preview')}>
          <p className="truncate text-xs text-gray-500">{origin}{activePath}</p>
          <p className="truncate text-base text-blue-700">{previewTitle}</p>
          <p className="line-clamp-2 text-sm text-gray-600">{form.description || t('adminContent.previewDesc')}</p>
        </div>

        {error && <p role="alert" className="text-sm text-red-600">{error}</p>}
        {done && <p role="status" className="text-sm text-green-700">{t('adminContent.seoSaved')}</p>}
        <button type="submit" disabled={saving} className="rounded bg-brand px-4 py-2 text-sm font-medium text-white disabled:opacity-40">
          {saving ? t('adminContent.saving') : t('adminContent.save')}
        </button>
      </form>
      <p className="mt-3 text-xs text-gray-500">{t('adminContent.customMarker')}</p>
    </div>
  )
}
