import { useEffect, useState } from 'react'
import { adminCreateCategory, adminDeleteCategory, adminListCategories, adminUpdateCategory } from '../../api/admin'
import { errorMessage } from '../../api/client'

const emptyForm = { name: '', slug: '', parent_id: '' }

function flatten(nodes, depth = 0) {
  return nodes.flatMap((n) => [{ ...n, depth }, ...flatten(n.children || [], depth + 1)])
}

export default function AdminCategories() {
  const [tree, setTree] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [editingId, setEditingId] = useState(null)
  const [form, setForm] = useState(emptyForm)
  const [formOpen, setFormOpen] = useState(false)
  const [formError, setFormError] = useState(null)
  const [submitting, setSubmitting] = useState(false)

  const load = () => adminListCategories().then(setTree).catch((err) => setError(errorMessage(err, 'Failed to load categories'))).finally(() => setLoading(false))

  useEffect(() => { load() }, [])

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
      setFormError(errorMessage(err, 'Failed to save category'))
    } finally {
      setSubmitting(false)
    }
  }

  const handleDelete = async (id) => {
    try {
      await adminDeleteCategory(id)
      await load()
    } catch (err) {
      setError(errorMessage(err, 'Failed to delete category'))
    }
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-2xl font-bold">Categories</h1>
        {!formOpen && <button onClick={openNew} className="bg-brand text-white px-4 py-2 rounded text-sm font-medium">Add Category</button>}
      </div>

      {loading && <p>Loading...</p>}
      {error && <p className="text-red-600 text-sm mb-3">{error}</p>}

      {formOpen && (
        <form onSubmit={handleSubmit} className="border border-gray-200 rounded-lg p-4 mb-6 space-y-3">
          <input required placeholder="Name" value={form.name} onChange={update('name')} className="w-full border border-gray-300 rounded px-3 py-2 text-sm" />
          <input required placeholder="Slug" value={form.slug} onChange={update('slug')} className="w-full border border-gray-300 rounded px-3 py-2 text-sm" />
          <select value={form.parent_id} onChange={update('parent_id')} className="w-full border border-gray-300 rounded px-3 py-2 text-sm">
            <option value="">No parent (top level)</option>
            {flat.filter((c) => c.id !== editingId).map((c) => (
              <option key={c.id} value={c.id}>{'  '.repeat(c.depth)}{c.name}</option>
            ))}
          </select>
          {formError && <p className="text-sm text-red-600">{formError}</p>}
          <div className="flex gap-2">
            <button type="submit" disabled={submitting} className="bg-brand text-white px-4 py-2 rounded text-sm font-medium disabled:opacity-40">
              {submitting ? 'Saving...' : 'Save'}
            </button>
            <button type="button" onClick={() => setFormOpen(false)} className="border border-gray-300 rounded px-4 py-2 text-sm">Cancel</button>
          </div>
        </form>
      )}

      {!loading && (
        <ul className="border border-gray-200 rounded-lg divide-y divide-gray-100">
          {flat.map((c) => (
            <li key={c.id} className="px-3 py-2 flex justify-between items-center text-sm" style={{ paddingLeft: `${12 + c.depth * 20}px` }}>
              <span>{c.name} <span className="text-gray-400">({c.slug})</span></span>
              <span className="flex gap-3">
                <button onClick={() => openEdit(c)} className="text-brand">Edit</button>
                <button onClick={() => handleDelete(c.id)} className="text-red-500">Delete</button>
              </span>
            </li>
          ))}
          {flat.length === 0 && <li className="px-3 py-6 text-center text-gray-400">No categories found.</li>}
        </ul>
      )}
    </div>
  )
}
