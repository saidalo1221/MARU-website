import { useEffect, useState } from 'react'
import { adminCreateTaxRule, adminListTaxRules, adminUpdateTaxRule } from '../../api/admin'
import { errorMessage } from '../../api/client'

const emptyForm = { country: '', customer_type: '', tax_type: 'vat', rate: 0, is_active: true }

// Pass '*' for country or customer_type to mean "any" (same wildcard
// convention as shipping rates).
export default function AdminTaxRules() {
  const [rules, setRules] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [editingId, setEditingId] = useState(null)
  const [form, setForm] = useState(emptyForm)
  const [formOpen, setFormOpen] = useState(false)
  const [formError, setFormError] = useState(null)
  const [submitting, setSubmitting] = useState(false)

  const load = () => adminListTaxRules().then(setRules).catch((err) => setError(errorMessage(err, 'Failed to load tax rules'))).finally(() => setLoading(false))
  useEffect(() => { load() }, [])

  const update = (field) => (e) => {
    const value = e.target.type === 'checkbox' ? e.target.checked : e.target.value
    setForm((f) => ({ ...f, [field]: value }))
  }

  const openNew = () => { setEditingId(null); setForm(emptyForm); setFormError(null); setFormOpen(true) }
  const openEdit = (r) => {
    setEditingId(r.id)
    setForm({ country: r.country, customer_type: r.customer_type, tax_type: r.tax_type, rate: r.rate, is_active: r.is_active })
    setFormError(null)
    setFormOpen(true)
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setFormError(null)
    setSubmitting(true)
    try {
      const payload = { rate: Number(form.rate), is_active: form.is_active }
      if (editingId) {
        await adminUpdateTaxRule(editingId, payload)
      } else {
        await adminCreateTaxRule({ ...payload, country: form.country, customer_type: form.customer_type, tax_type: form.tax_type })
      }
      setFormOpen(false)
      await load()
    } catch (err) {
      setFormError(errorMessage(err, 'Failed to save tax rule'))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-2xl font-bold">Tax Rules</h1>
        {!formOpen && <button onClick={openNew} className="bg-brand text-white px-4 py-2 rounded text-sm font-medium">Add Rule</button>}
      </div>

      {loading && <p>Loading...</p>}
      {error && <p className="text-red-600 text-sm mb-3">{error}</p>}

      {formOpen && (
        <form onSubmit={handleSubmit} className="border border-gray-200 rounded-lg p-4 mb-6 grid grid-cols-2 gap-3">
          <input required disabled={!!editingId} placeholder="Country (or * for any)" value={form.country} onChange={update('country')} className="border border-gray-300 rounded px-3 py-2 text-sm disabled:bg-gray-100" />
          <input required disabled={!!editingId} placeholder="Customer type (or * for any)" value={form.customer_type} onChange={update('customer_type')} className="border border-gray-300 rounded px-3 py-2 text-sm disabled:bg-gray-100" />
          <input disabled={!!editingId} placeholder="Tax type" value={form.tax_type} onChange={update('tax_type')} className="border border-gray-300 rounded px-3 py-2 text-sm disabled:bg-gray-100" />
          <input required type="number" step="0.01" min="0" max="100" placeholder="Rate (%)" value={form.rate} onChange={update('rate')} className="border border-gray-300 rounded px-3 py-2 text-sm" />
          <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={form.is_active} onChange={update('is_active')} /> Active</label>
          {formError && <p className="text-sm text-red-600 col-span-2">{formError}</p>}
          <div className="col-span-2 flex gap-2">
            <button type="submit" disabled={submitting} className="bg-brand text-white px-4 py-2 rounded text-sm font-medium disabled:opacity-40">{submitting ? 'Saving...' : 'Save'}</button>
            <button type="button" onClick={() => setFormOpen(false)} className="border border-gray-300 rounded px-4 py-2 text-sm">Cancel</button>
          </div>
        </form>
      )}

      {!loading && (
        <div className="border border-gray-200 rounded-lg overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-left">
              <tr><th className="px-3 py-2">Country</th><th className="px-3 py-2">Customer type</th><th className="px-3 py-2">Tax type</th><th className="px-3 py-2">Rate</th><th className="px-3 py-2">Active</th><th className="px-3 py-2"></th></tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {rules.map((r) => (
                <tr key={r.id} className="hover:bg-gray-50">
                  <td className="px-3 py-2">{r.country}</td>
                  <td className="px-3 py-2">{r.customer_type}</td>
                  <td className="px-3 py-2">{r.tax_type}</td>
                  <td className="px-3 py-2">{Number(r.rate)}%</td>
                  <td className="px-3 py-2">{r.is_active ? 'Yes' : 'No'}</td>
                  <td className="px-3 py-2 text-right"><button onClick={() => openEdit(r)} className="text-brand">Edit</button></td>
                </tr>
              ))}
              {rules.length === 0 && <tr><td colSpan={6} className="px-3 py-6 text-center text-gray-400">No tax rules found.</td></tr>}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
