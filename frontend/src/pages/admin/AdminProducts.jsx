import { useEffect, useState } from 'react'
import { adminCreateProduct, adminListCategories, adminListProducts, adminUpdateProduct } from '../../api/admin'
import { errorMessage } from '../../api/client'

const emptyForm = { category_id: '', name: '', slug: '', volume_ml: '', shape: '', purpose: '', description: '', country_of_origin: '', min_order_quantity: 1 }

function flattenCategories(nodes, depth = 0) {
  return nodes.flatMap((n) => [{ ...n, depth }, ...flattenCategories(n.children || [], depth + 1)])
}

// List + basic field editing only. Variants, SKUs, pricing, and inventory
// are managed elsewhere (POST /admin/products/{id}/variants, /admin/skus,
// /admin/inventory) and don't have an admin UI yet — see TODO.md.
export default function AdminProducts() {
  const [products, setProducts] = useState([])
  const [categories, setCategories] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [editingId, setEditingId] = useState(null)
  const [form, setForm] = useState(emptyForm)
  const [formOpen, setFormOpen] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [formError, setFormError] = useState(null)

  const load = () => Promise.all([adminListProducts(), adminListCategories()])
    .then(([p, c]) => { setProducts(p); setCategories(flattenCategories(c)) })
    .catch((err) => setError(errorMessage(err, 'Failed to load products')))
    .finally(() => setLoading(false))

  useEffect(() => { load() }, [])

  const update = (field) => (e) => setForm((f) => ({ ...f, [field]: e.target.value }))

  const openNew = () => { setEditingId(null); setForm(emptyForm); setFormError(null); setFormOpen(true) }
  const openEdit = (p) => {
    setEditingId(p.id)
    setForm({
      category_id: p.category_id, name: p.name, slug: p.slug, volume_ml: p.volume_ml,
      shape: p.shape || '', purpose: p.purpose || '', description: p.description || '',
      country_of_origin: p.country_of_origin || '', min_order_quantity: p.min_order_quantity,
    })
    setFormError(null)
    setFormOpen(true)
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setFormError(null)
    setSubmitting(true)
    try {
      const payload = { ...form, category_id: Number(form.category_id), volume_ml: Number(form.volume_ml), min_order_quantity: Number(form.min_order_quantity) }
      if (editingId) await adminUpdateProduct(editingId, payload)
      else await adminCreateProduct(payload)
      setFormOpen(false)
      await load()
    } catch (err) {
      setFormError(errorMessage(err, 'Failed to save product'))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-2xl font-bold">Products</h1>
        {!formOpen && <button onClick={openNew} className="bg-brand text-white px-4 py-2 rounded text-sm font-medium">Add Product</button>}
      </div>

      {loading && <p>Loading...</p>}
      {error && <p className="text-red-600 text-sm">{error}</p>}

      {formOpen && (
        <form onSubmit={handleSubmit} className="border border-gray-200 rounded-lg p-4 mb-6 grid grid-cols-2 gap-3">
          <select required value={form.category_id} onChange={update('category_id')} className="border border-gray-300 rounded px-3 py-2 text-sm col-span-2">
            <option value="">Select category</option>
            {categories.map((c) => <option key={c.id} value={c.id}>{'  '.repeat(c.depth)}{c.name}</option>)}
          </select>
          <input required placeholder="Name" value={form.name} onChange={update('name')} className="border border-gray-300 rounded px-3 py-2 text-sm" />
          <input required placeholder="Slug" value={form.slug} onChange={update('slug')} className="border border-gray-300 rounded px-3 py-2 text-sm" />
          <input required type="number" min="1" placeholder="Volume (ml)" value={form.volume_ml} onChange={update('volume_ml')} className="border border-gray-300 rounded px-3 py-2 text-sm" />
          <input type="number" min="1" placeholder="Min order quantity" value={form.min_order_quantity} onChange={update('min_order_quantity')} className="border border-gray-300 rounded px-3 py-2 text-sm" />
          <input placeholder="Shape" value={form.shape} onChange={update('shape')} className="border border-gray-300 rounded px-3 py-2 text-sm" />
          <input placeholder="Purpose" value={form.purpose} onChange={update('purpose')} className="border border-gray-300 rounded px-3 py-2 text-sm" />
          <input placeholder="Country of origin" value={form.country_of_origin} onChange={update('country_of_origin')} className="border border-gray-300 rounded px-3 py-2 text-sm col-span-2" />
          <textarea placeholder="Description" value={form.description} onChange={update('description')} rows={3} className="border border-gray-300 rounded px-3 py-2 text-sm col-span-2" />
          {formError && <p className="text-sm text-red-600 col-span-2">{formError}</p>}
          <div className="col-span-2 flex gap-2">
            <button type="submit" disabled={submitting} className="bg-brand text-white px-4 py-2 rounded text-sm font-medium disabled:opacity-40">
              {submitting ? 'Saving...' : 'Save'}
            </button>
            <button type="button" onClick={() => setFormOpen(false)} className="border border-gray-300 rounded px-4 py-2 text-sm">Cancel</button>
          </div>
        </form>
      )}

      {!loading && !error && (
        <div className="border border-gray-200 rounded-lg overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-left">
              <tr><th className="px-3 py-2">Name</th><th className="px-3 py-2">Slug</th><th className="px-3 py-2">Volume</th><th className="px-3 py-2">Variants</th><th className="px-3 py-2"></th></tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {products.map((p) => (
                <tr key={p.id} className="hover:bg-gray-50">
                  <td className="px-3 py-2">{p.name}</td>
                  <td className="px-3 py-2 text-gray-500">{p.slug}</td>
                  <td className="px-3 py-2">{p.volume_ml} ml</td>
                  <td className="px-3 py-2">{p.variants.length}</td>
                  <td className="px-3 py-2 text-right"><button onClick={() => openEdit(p)} className="text-brand">Edit</button></td>
                </tr>
              ))}
              {products.length === 0 && <tr><td colSpan={5} className="px-3 py-6 text-center text-gray-400">No products found.</td></tr>}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
