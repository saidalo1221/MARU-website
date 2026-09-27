import { useEffect, useState } from 'react'
import { adminCreateWarehouse, adminListWarehouses, adminUpdateWarehouse } from '../../api/admin'
import { errorMessage } from '../../api/client'

const emptyForm = { name: '', country: '', address: '', priority: 100, is_active: true }

export default function AdminWarehouses() {
  const [warehouses, setWarehouses] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [editingId, setEditingId] = useState(null)
  const [form, setForm] = useState(emptyForm)
  const [formOpen, setFormOpen] = useState(false)
  const [formError, setFormError] = useState(null)
  const [submitting, setSubmitting] = useState(false)

  const load = () => adminListWarehouses().then(setWarehouses).catch((err) => setError(errorMessage(err, 'Failed to load warehouses'))).finally(() => setLoading(false))

  useEffect(() => { load() }, [])

  const update = (field) => (e) => {
    const value = e.target.type === 'checkbox' ? e.target.checked : e.target.value
    setForm((f) => ({ ...f, [field]: value }))
  }

  const openNew = () => { setEditingId(null); setForm(emptyForm); setFormError(null); setFormOpen(true) }
  const openEdit = (w) => { setEditingId(w.id); setForm({ name: w.name, country: w.country, address: w.address || '', priority: w.priority, is_active: w.is_active }); setFormError(null); setFormOpen(true) }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setFormError(null)
    setSubmitting(true)
    try {
      const payload = { ...form, priority: Number(form.priority) }
      if (editingId) await adminUpdateWarehouse(editingId, payload)
      else await adminCreateWarehouse(payload)
      setFormOpen(false)
      await load()
    } catch (err) {
      setFormError(errorMessage(err, 'Failed to save warehouse'))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-2xl font-bold">Warehouses</h1>
        {!formOpen && <button onClick={openNew} className="bg-brand text-white px-4 py-2 rounded text-sm font-medium">Add Warehouse</button>}
      </div>

      {loading && <p>Loading...</p>}
      {error && <p className="text-red-600 text-sm mb-3">{error}</p>}

      {formOpen && (
        <form onSubmit={handleSubmit} className="border border-gray-200 rounded-lg p-4 mb-6 space-y-3">
          <input required placeholder="Name" value={form.name} onChange={update('name')} className="w-full border border-gray-300 rounded px-3 py-2 text-sm" />
          <input required placeholder="Country" value={form.country} onChange={update('country')} className="w-full border border-gray-300 rounded px-3 py-2 text-sm" />
          <input placeholder="Address" value={form.address} onChange={update('address')} className="w-full border border-gray-300 rounded px-3 py-2 text-sm" />
          <div>
            <label className="block text-xs text-gray-500 mb-1">Priority (lower = picked first)</label>
            <input type="number" min="0" value={form.priority} onChange={update('priority')} className="w-full border border-gray-300 rounded px-3 py-2 text-sm" />
          </div>
          <label className="flex items-center gap-2 text-sm">
            <input type="checkbox" checked={form.is_active} onChange={update('is_active')} /> Active
          </label>
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
        <div className="border border-gray-200 rounded-lg overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-left">
              <tr><th className="px-3 py-2">Name</th><th className="px-3 py-2">Country</th><th className="px-3 py-2">Priority</th><th className="px-3 py-2">Active</th><th className="px-3 py-2"></th></tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {warehouses.map((w) => (
                <tr key={w.id} className="hover:bg-gray-50">
                  <td className="px-3 py-2">{w.name}</td>
                  <td className="px-3 py-2">{w.country}</td>
                  <td className="px-3 py-2">{w.priority}</td>
                  <td className="px-3 py-2">{w.is_active ? 'Yes' : 'No'}</td>
                  <td className="px-3 py-2 text-right"><button onClick={() => openEdit(w)} className="text-brand">Edit</button></td>
                </tr>
              ))}
              {warehouses.length === 0 && <tr><td colSpan={5} className="px-3 py-6 text-center text-gray-400">No warehouses found.</td></tr>}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
