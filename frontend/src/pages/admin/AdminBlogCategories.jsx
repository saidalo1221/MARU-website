import { useEffect, useState } from 'react'
import {
  adminCreateBlogCategory,
  adminDeleteBlogCategory,
  adminListBlogCategories,
  adminUpdateBlogCategory,
} from '../../api/admin'
import { errorMessage } from '../../api/client'
import { useLocale } from '../../context/LocaleContext'

const emptyForm = { name: '', slug: '' }

export default function AdminBlogCategories() {
  const { t } = useLocale()
  const [categories, setCategories] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [editingId, setEditingId] = useState(null)
  const [form, setForm] = useState(emptyForm)
  const [formOpen, setFormOpen] = useState(false)
  const [formError, setFormError] = useState(null)
  const [submitting, setSubmitting] = useState(false)

  const load = () =>
    adminListBlogCategories()
      .then(setCategories)
      .catch((err) => setError(errorMessage(err, t('admin.blog.loadFailed'))))
      .finally(() => setLoading(false))

  useEffect(() => { load() }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const update = (field) => (e) => setForm((f) => ({ ...f, [field]: e.target.value }))

  const openNew = () => { setEditingId(null); setForm(emptyForm); setFormError(null); setFormOpen(true) }
  const openEdit = (c) => { setEditingId(c.id); setForm({ name: c.name, slug: c.slug }); setFormError(null); setFormOpen(true) }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setFormError(null)
    setSubmitting(true)
    try {
      if (editingId) await adminUpdateBlogCategory(editingId, form)
      else await adminCreateBlogCategory(form)
      setFormOpen(false)
      await load()
    } catch (err) {
      setFormError(errorMessage(err, t('admin.blog.saveFailed')))
    } finally {
      setSubmitting(false)
    }
  }

  const handleDelete = async (id) => {
    try {
      await adminDeleteBlogCategory(id)
      await load()
    } catch (err) {
      setError(errorMessage(err, t('admin.blog.deleteFailed')))
    }
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-2xl font-bold">{t('admin.blog.categoriesTitle')}</h1>
        {!formOpen && <button onClick={openNew} className="bg-brand text-white px-4 py-2 rounded text-sm font-medium">{t('admin.blog.addCategory')}</button>}
      </div>

      {loading && <p>{t('admin.common.loading')}</p>}
      {error && <p className="text-red-600 text-sm mb-3">{error}</p>}

      {formOpen && (
        <form onSubmit={handleSubmit} className="border border-gray-200 rounded-lg p-4 mb-6 space-y-3">
          <input required placeholder={t('admin.common.name')} value={form.name} onChange={update('name')} className="w-full border border-gray-300 rounded px-3 py-2 text-sm" />
          <input required placeholder={t('admin.blog.slug')} value={form.slug} onChange={update('slug')} className="w-full border border-gray-300 rounded px-3 py-2 text-sm" />
          {formError && <p className="text-sm text-red-600">{formError}</p>}
          <div className="flex gap-2">
            <button type="submit" disabled={submitting} className="bg-brand text-white px-4 py-2 rounded text-sm font-medium disabled:opacity-40">
              {submitting ? t('admin.common.saving') : t('admin.common.save')}
            </button>
            <button type="button" onClick={() => setFormOpen(false)} className="border border-gray-300 rounded px-4 py-2 text-sm">{t('admin.common.cancel')}</button>
          </div>
        </form>
      )}

      {!loading && (
        <ul className="border border-gray-200 rounded-lg divide-y divide-gray-100">
          {categories.map((c) => (
            <li key={c.id} className="px-3 py-2 flex justify-between items-center text-sm">
              <span>{c.name} <span className="text-gray-400">({c.slug})</span></span>
              <span className="flex gap-3">
                <button onClick={() => openEdit(c)} className="text-brand">{t('admin.common.edit')}</button>
                <button onClick={() => handleDelete(c.id)} className="text-red-500">{t('admin.common.delete')}</button>
              </span>
            </li>
          ))}
          {categories.length === 0 && <li className="px-3 py-6 text-center text-gray-400">{t('admin.blog.noneCategories')}</li>}
        </ul>
      )}
    </div>
  )
}
