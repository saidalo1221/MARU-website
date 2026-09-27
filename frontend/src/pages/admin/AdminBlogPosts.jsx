import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { adminCreateBlogPost, adminListBlogCategories, adminListBlogPosts } from '../../api/admin'
import { errorMessage } from '../../api/client'
import { useLocale } from '../../context/LocaleContext'

const emptyForm = { category_id: '', slug: '', title: '', excerpt: '', content: '', cover_image_url: '', author_name: '' }

export default function AdminBlogPosts() {
  const { t } = useLocale()
  const [posts, setPosts] = useState([])
  const [categories, setCategories] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [form, setForm] = useState(emptyForm)
  const [formOpen, setFormOpen] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [formError, setFormError] = useState(null)

  const load = () =>
    Promise.all([adminListBlogPosts(), adminListBlogCategories()])
      .then(([p, c]) => { setPosts(p); setCategories(c) })
      .catch((err) => setError(errorMessage(err, t('admin.blog.loadFailed'))))
      .finally(() => setLoading(false))

  useEffect(() => { load() }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const update = (field) => (e) => setForm((f) => ({ ...f, [field]: e.target.value }))

  const openNew = () => { setForm(emptyForm); setFormError(null); setFormOpen(true) }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setFormError(null)
    setSubmitting(true)
    try {
      const payload = {
        ...form,
        category_id: Number(form.category_id),
        excerpt: form.excerpt || null,
        cover_image_url: form.cover_image_url || null,
        author_name: form.author_name || null,
      }
      await adminCreateBlogPost(payload)
      setFormOpen(false)
      await load()
    } catch (err) {
      setFormError(errorMessage(err, t('admin.blog.saveFailed')))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-2xl font-bold">{t('admin.blog.postsTitle')}</h1>
        {!formOpen && <button onClick={openNew} className="bg-brand text-white px-4 py-2 rounded text-sm font-medium">{t('admin.blog.addPost')}</button>}
      </div>

      {loading && <p>{t('admin.common.loading')}</p>}
      {error && <p className="text-red-600 text-sm">{error}</p>}

      {formOpen && (
        <form onSubmit={handleSubmit} className="border border-gray-200 rounded-lg p-4 mb-6 grid grid-cols-2 gap-3">
          <select required value={form.category_id} onChange={update('category_id')} className="border border-gray-300 rounded px-3 py-2 text-sm col-span-2">
            <option value="">{t('admin.blog.category')}</option>
            {categories.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
          </select>
          <input required placeholder={t('admin.blog.post') + ' — ' + t('admin.common.name')} value={form.title} onChange={update('title')} className="border border-gray-300 rounded px-3 py-2 text-sm" />
          <input required placeholder={t('admin.blog.slug')} value={form.slug} onChange={update('slug')} className="border border-gray-300 rounded px-3 py-2 text-sm" />
          <input placeholder={t('admin.blog.authorName')} value={form.author_name} onChange={update('author_name')} className="border border-gray-300 rounded px-3 py-2 text-sm" />
          <input placeholder={t('admin.blog.coverImageUrl')} value={form.cover_image_url} onChange={update('cover_image_url')} className="border border-gray-300 rounded px-3 py-2 text-sm" />
          <textarea placeholder={t('admin.blog.excerpt')} value={form.excerpt} onChange={update('excerpt')} rows={2} className="border border-gray-300 rounded px-3 py-2 text-sm col-span-2" />
          <textarea required placeholder={t('admin.blog.content')} value={form.content} onChange={update('content')} rows={6} className="border border-gray-300 rounded px-3 py-2 text-sm col-span-2" />
          {formError && <p className="text-sm text-red-600 col-span-2">{formError}</p>}
          <div className="col-span-2 flex gap-2">
            <button type="submit" disabled={submitting} className="bg-brand text-white px-4 py-2 rounded text-sm font-medium disabled:opacity-40">
              {submitting ? t('admin.common.saving') : t('admin.common.save')}
            </button>
            <button type="button" onClick={() => setFormOpen(false)} className="border border-gray-300 rounded px-4 py-2 text-sm">{t('admin.common.cancel')}</button>
          </div>
        </form>
      )}

      {!loading && !error && (
        <div className="border border-gray-200 rounded-lg overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-left">
              <tr>
                <th className="px-3 py-2">{t('admin.common.name')}</th>
                <th className="px-3 py-2">{t('admin.blog.category')}</th>
                <th className="px-3 py-2">{t('admin.blog.published')}</th>
                <th className="px-3 py-2"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {posts.map((p) => (
                <tr key={p.id} className="hover:bg-gray-50">
                  <td className="px-3 py-2">{p.title}</td>
                  <td className="px-3 py-2 text-gray-500">{categories.find((c) => c.id === p.category_id)?.name ?? '—'}</td>
                  <td className="px-3 py-2">{p.is_published ? t('admin.common.yes') : t('admin.common.no')}</td>
                  <td className="px-3 py-2 text-right"><Link to={`/admin/blog/posts/${p.id}`} className="text-brand">{t('admin.common.edit')}</Link></td>
                </tr>
              ))}
              {posts.length === 0 && <tr><td colSpan={4} className="px-3 py-6 text-center text-gray-400">{t('admin.blog.none')}</td></tr>}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
