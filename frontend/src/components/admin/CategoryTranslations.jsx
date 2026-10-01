import { useEffect, useState } from 'react'
import { adminListCategoryTranslations, adminUpsertCategoryTranslation } from '../../api/admin'
import { errorMessage } from '../../api/client'
import { useLocale } from '../../context/LocaleContext'
import Tabs from '../ui/Tabs'

const LOCALES = ['ru', 'uz', 'en']
const empty = { name: '', description: '', seo_content: '' }
const inputCls = 'w-full border border-gray-300 rounded px-3 py-2 text-sm'

// Per-language name, description and SEO text of a category (PRD ТЗ№2 §10, ТЗ№3 §71).
export default function CategoryTranslations({ categoryId }) {
  const { t } = useLocale()
  const [active, setActive] = useState('ru')
  const [rows, setRows] = useState({})
  const [form, setForm] = useState(empty)
  const [error, setError] = useState(null)
  const [saved, setSaved] = useState(false)
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    adminListCategoryTranslations(categoryId)
      .then((list) => setRows(Object.fromEntries(list.map((r) => [r.locale, r]))))
      .catch((err) => setError(errorMessage(err, t('admin.categories.translationsFailed'))))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [categoryId])

  useEffect(() => {
    const row = rows[active]
    setForm(row ? { name: row.name, description: row.description || '', seo_content: row.seo_content || '' } : empty)
    setSaved(false)
  }, [active, rows])

  const update = (field) => (e) => {
    setSaved(false)
    setForm((f) => ({ ...f, [field]: e.target.value }))
  }

  const save = async (e) => {
    e.preventDefault()
    setError(null)
    setBusy(true)
    try {
      const row = await adminUpsertCategoryTranslation(categoryId, active, {
        name: form.name,
        description: form.description || null,
        seo_content: form.seo_content || null,
      })
      setRows((r) => ({ ...r, [active]: row }))
      setSaved(true)
    } catch (err) {
      setError(errorMessage(err, t('admin.categories.translationsFailed')))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="border-t border-gray-100 pt-3">
      <p className="text-sm font-medium mb-2">{t('admin.categories.translations')}</p>
      <div className="mb-3">
        <Tabs label={t('admin.categories.translations')} active={active} onChange={setActive} items={LOCALES.map((l) => ({ key: l, label: l.toUpperCase() }))} />
      </div>
      <div className="space-y-2">
        <input required placeholder={t('admin.common.name')} aria-label={t('admin.common.name')} value={form.name} onChange={update('name')} className={inputCls} />
        <textarea placeholder={t('admin.categories.description')} aria-label={t('admin.categories.description')} value={form.description} onChange={update('description')} rows={3} className={inputCls} />
        <textarea placeholder={t('admin.categories.seoContent')} aria-label={t('admin.categories.seoContent')} value={form.seo_content} onChange={update('seo_content')} rows={4} className={inputCls} />
        {error && <p role="alert" className="text-sm text-red-600">{error}</p>}
        {saved && <p role="status" className="text-sm text-green-700">{t('admin.productDetail.tiersSaved')}</p>}
        <button type="button" onClick={save} disabled={busy || !form.name} className="bg-brand text-white px-3 py-1.5 rounded text-sm disabled:opacity-40">
          {t('admin.common.save')}
        </button>
      </div>
    </div>
  )
}
