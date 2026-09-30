import { useEffect, useState } from 'react'
import { adminCreateCategory, adminDeleteCategory, adminListCategories, adminUpdateCategory } from '../../api/admin'
import { errorMessage } from '../../api/client'
import { useLocale } from '../../context/LocaleContext'

const emptyForm = { name: '', slug: '', parent_id: '' }

function flatten(nodes, depth = 0) {
  return nodes.flatMap((n) => [{ ...n, depth }, ...flatten(n.children || [], depth + 1)])
}

export default function AdminCategories() {
  const { t } = useLocale()
  const [tree, setTree] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [editingId, setEditingId] = useState(null)
  const [form, setForm] = useState(emptyForm)
  const [formOpen, setFormOpen] = useState(false)
  const [formError, setFormError] = useState(null)
  const [submitting, setSubmitting] = useState(false)

  const load = () => adminListCategories().then(setTree).catch((err) => setError(errorMessage(err, t('admin.categories.loadFailed')))).finally(() => setLoading(false))

  useEffect(() => { load() }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const flat = flatten(tree)
  const update = (field) => (e) => setForm((f) => ({ ...f, [field]: e.target.value }))

  const openNew = () => { setEditingId(null); setForm(emptyForm); setFormError(null); setFormOpen(true) }
  const openEdit = (c) => { setEditingId(c.id); setForm({ name: c.name, slug: c.slug, parent_id: c.parent_id ?? '' }); setFormError(null); setFormOpen(true) }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setFormError(null)
    setSubmitting(true)
    try {
      const payload = { name: form.name, slug: form.slug, parent_id: form.parent_id === '' ? null : Number(form.parent_id) }
      if (editingId) await adminUpdateCategory(editingId, payload)
      else await adminCreateCategory(payload)
      setFormOpen(false)
      await load()
    } catch (err) {
      setFormError(errorMessage(err, t('admin.categories.saveFailed')))
    } finally {
      setSubmitting(false)
    }
  }

  const handleDelete = async (id) => {
    try {
      await adminDeleteCategory(id)
      await load()
    } catch (err) {
      setError(errorMessage(err, t('admin.categories.deleteFailed')))
    }
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-2xl font-bold">{t('admin.categories.title')}</h1>
        {!formOpen && <button onClick={openNew} className="bg-brand text-white px-4 py-2 rounded text-sm font-medium">{t('admin.categories.add')}</button>}
      </div>

      {loading && <p>{t('admin.common.loading')}</p>}
      {error && <p role="alert" className="text-red-600 text-sm mb-3">{error}</p>}

      {formOpen && (
        <form onSubmit={handleSubmit} className="border border-gray-200 rounded-lg p-4 mb-6 space-y-3">
          <input required placeholder={t('admin.common.name')} aria-label={t('admin.common.name')} value={form.name} onChange={update('name')} className="w-full border border-gray-300 rounded px-3 py-2 text-sm" />
          <input required placeholder={t('admin.common.slug')} aria-label={t('admin.common.slug')} value={form.slug} onChange={update('slug')} className="w-full border border-gray-300 rounded px-3 py-2 text-sm" />
          <select value={form.parent_id} aria-label={t('admin.categories.noParent')} onChange={update('parent_id')} className="w-full border border-gray-300 rounded px-3 py-2 text-sm">
            <option value="">{t('admin.categories.noParent')}</option>
            {flat.filter((c) => c.id !== editingId).map((c) => (
              <option key={c.id} value={c.id}>{'  '.repeat(c.depth)}{c.name}</option>
            ))}
          </select>
          {formError && <p role="alert" className="text-sm text-red-600">{formError}</p>}
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
          {flat.map((c) => (
            <li key={c.id} className="px-3 py-2 flex justify-between items-center text-sm" style={{ paddingLeft: `${12 + c.depth * 20}px` }}>
              <span>{c.name} <span className="text-gray-500">({c.slug})</span></span>
              <span className="flex gap-3">
                <button onClick={() => openEdit(c)} className="text-brand">{t('admin.common.edit')}</button>
                <button onClick={() => handleDelete(c.id)} className="text-red-600">{t('admin.common.delete')}</button>
              </span>
            </li>
          ))}
          {flat.length === 0 && <li className="px-3 py-6 text-center text-gray-500">{t('admin.categories.none')}</li>}
        </ul>
      )}
    </div>
  )
}
