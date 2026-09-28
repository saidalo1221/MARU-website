import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import {
  adminDeleteBlogPost,
  adminGetBlogPost,
  adminListBlogCategories,
  adminListBlogPostTranslations,
  adminUpdateBlogPost,
  adminUploadImage,
  adminUpsertBlogPostTranslation,
} from '../../api/admin'
import { errorMessage } from '../../api/client'
import { useLocale } from '../../context/LocaleContext'

const LOCALES = ['ru', 'uz', 'en']
const emptyTranslation = { slug: '', title: '', excerpt: '', content: '' }

export default function AdminBlogPostDetail() {
  const { postId } = useParams()
  const navigate = useNavigate()
  const { t } = useLocale()

  const [post, setPost] = useState(null)
  const [categories, setCategories] = useState([])
  const [form, setForm] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [saving, setSaving] = useState(false)
  const [saveError, setSaveError] = useState(null)
  const [uploading, setUploading] = useState(false)
  const [uploadError, setUploadError] = useState(null)

  const [activeLocale, setActiveLocale] = useState('ru')
  const [translations, setTranslations] = useState({})
  const [translationForm, setTranslationForm] = useState(emptyTranslation)
  const [translationSaving, setTranslationSaving] = useState(false)
  const [translationError, setTranslationError] = useState(null)

  const load = () =>
    Promise.all([adminGetBlogPost(postId), adminListBlogCategories(), adminListBlogPostTranslations(postId)])
      .then(([p, c, tr]) => {
        setPost(p)
        setForm({
          category_id: p.category_id,
          slug: p.slug,
          title: p.title,
          excerpt: p.excerpt || '',
          content: p.content,
          cover_image_url: p.cover_image_url || '',
          author_name: p.author_name || '',
          is_published: p.is_published,
        })
        setCategories(c)
        const byLocale = Object.fromEntries(tr.map((row) => [row.locale, row]))
        setTranslations(byLocale)
      })
      .catch((err) => setError(errorMessage(err, t('admin.blog.loadFailed'))))
      .finally(() => setLoading(false))

  useEffect(() => { load() }, [postId]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    const existing = translations[activeLocale]
    setTranslationForm(existing ? { slug: existing.slug || '', title: existing.title, excerpt: existing.excerpt || '', content: existing.content } : emptyTranslation)
    setTranslationError(null)
  }, [activeLocale, translations])

  if (loading) return <p>{t('admin.common.loading')}</p>
  if (error) return <p className="text-red-600 text-sm">{error}</p>
  if (!post || !form) return null

  const update = (field) => (e) => {
    const value = field === 'is_published' ? e.target.checked : e.target.value
    setForm((f) => ({ ...f, [field]: value }))
  }

  const handleSave = async (e) => {
    e.preventDefault()
    setSaveError(null)
    setSaving(true)
    try {
      const payload = {
        ...form,
        category_id: Number(form.category_id),
        excerpt: form.excerpt || null,
        cover_image_url: form.cover_image_url || null,
        author_name: form.author_name || null,
      }
      const updated = await adminUpdateBlogPost(postId, payload)
      setPost(updated)
    } catch (err) {
      setSaveError(errorMessage(err, t('admin.blog.saveFailed')))
    } finally {
      setSaving(false)
    }
  }

  const handleFileSelect = async (e) => {
    const file = e.target.files?.[0]
    if (!file) return
    setUploadError(null)
    setUploading(true)
    try {
      const { url } = await adminUploadImage(file)
      setForm((f) => ({ ...f, cover_image_url: url }))
    } catch (err) {
      setUploadError(errorMessage(err, t('admin.blog.uploadFailed')))
    } finally {
      setUploading(false)
      e.target.value = ''
    }
  }

  const handleDelete = async () => {
    try {
      await adminDeleteBlogPost(postId)
      navigate('/admin/blog/posts')
    } catch (err) {
      setError(errorMessage(err, t('admin.blog.deleteFailed')))
    }
  }

  const updateTranslation = (field) => (e) => setTranslationForm((f) => ({ ...f, [field]: e.target.value }))

  const handleTranslationSave = async (e) => {
    e.preventDefault()
    setTranslationError(null)
    setTranslationSaving(true)
    try {
      const payload = {
        slug: translationForm.slug || null,
        title: translationForm.title,
        excerpt: translationForm.excerpt || null,
        content: translationForm.content,
      }
      const saved = await adminUpsertBlogPostTranslation(postId, activeLocale, payload)
      setTranslations((t2) => ({ ...t2, [activeLocale]: saved }))
    } catch (err) {
      setTranslationError(errorMessage(err, t('admin.blog.saveFailed')))
    } finally {
      setTranslationSaving(false)
    }
  }

  return (
    <div>
      <button onClick={() => navigate('/admin/blog/posts')} className="text-xs text-gray-500 mb-3">{t('admin.blog.back')}</button>
      <h1 className="text-2xl font-bold mb-4">{post.title}</h1>

      <form onSubmit={handleSave} className="border border-gray-200 rounded-lg p-4 mb-8 grid grid-cols-2 gap-3">
        <select value={form.category_id} onChange={update('category_id')} className="border border-gray-300 rounded px-3 py-2 text-sm col-span-2">
          {categories.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
        </select>
        <input placeholder={t('admin.common.name')} value={form.title} onChange={update('title')} className="border border-gray-300 rounded px-3 py-2 text-sm" />
        <input placeholder={t('admin.blog.slug')} value={form.slug} onChange={update('slug')} className="border border-gray-300 rounded px-3 py-2 text-sm" />
        <input placeholder={t('admin.blog.authorName')} value={form.author_name} onChange={update('author_name')} className="border border-gray-300 rounded px-3 py-2 text-sm" />
        <div className="flex items-center gap-2">
          <input placeholder={t('admin.blog.coverImageUrl')} value={form.cover_image_url} onChange={update('cover_image_url')} className="flex-1 border border-gray-300 rounded px-3 py-2 text-sm" />
          <input type="file" accept="image/jpeg,image/png,image/webp,image/gif" onChange={handleFileSelect} disabled={uploading} className="text-xs w-28" />
        </div>
        {uploading && <p className="col-span-2 text-xs text-gray-500">{t('admin.blog.uploading')}</p>}
        {uploadError && <p className="col-span-2 text-xs text-red-600">{uploadError}</p>}
        {form.cover_image_url && (
          <img src={form.cover_image_url} alt="" className="col-span-2 h-24 object-cover rounded border border-gray-200" />
        )}
        <textarea placeholder={t('admin.blog.excerpt')} value={form.excerpt} onChange={update('excerpt')} rows={2} className="border border-gray-300 rounded px-3 py-2 text-sm col-span-2" />
        <textarea placeholder={t('admin.blog.content')} value={form.content} onChange={update('content')} rows={8} className="border border-gray-300 rounded px-3 py-2 text-sm col-span-2" />
        <label className="flex items-center gap-2 text-sm">
          <input type="checkbox" checked={form.is_published} onChange={update('is_published')} />
          {t('admin.blog.published')}
        </label>
        {saveError && <p className="text-sm text-red-600 col-span-2">{saveError}</p>}
        <div className="col-span-2 flex gap-2">
          <button type="submit" disabled={saving} className="bg-brand text-white px-4 py-2 rounded text-sm font-medium disabled:opacity-40">
            {saving ? t('admin.common.saving') : t('admin.common.save')}
          </button>
          <button type="button" onClick={handleDelete} className="border border-red-300 text-red-600 rounded px-4 py-2 text-sm">{t('admin.common.delete')}</button>
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
        <input placeholder={t('admin.blog.slugTranslated')} value={translationForm.slug} onChange={updateTranslation('slug')} className="w-full border border-gray-300 rounded px-3 py-2 text-sm" />
        <input required placeholder={t('admin.common.name')} value={translationForm.title} onChange={updateTranslation('title')} className="w-full border border-gray-300 rounded px-3 py-2 text-sm" />
        <textarea placeholder={t('admin.blog.excerpt')} value={translationForm.excerpt} onChange={updateTranslation('excerpt')} rows={2} className="w-full border border-gray-300 rounded px-3 py-2 text-sm" />
        <textarea required placeholder={t('admin.blog.content')} value={translationForm.content} onChange={updateTranslation('content')} rows={8} className="w-full border border-gray-300 rounded px-3 py-2 text-sm" />
        {translationError && <p className="text-sm text-red-600">{translationError}</p>}
        <button type="submit" disabled={translationSaving} className="bg-brand text-white px-4 py-2 rounded text-sm font-medium disabled:opacity-40">
          {translationSaving ? t('admin.common.saving') : t('admin.common.save')}
        </button>
      </form>
    </div>
  )
}
