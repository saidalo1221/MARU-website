import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import {
  adminAddInventory, adminCreateSku, adminCreateVariant, adminGetProduct, adminListInventory,
  adminListWarehouses, adminUpdateInventory, adminUpdateProduct, adminUpdateSku, adminUpdateVariant,
} from '../../api/admin'
import { errorMessage } from '../../api/client'
import { useLocale } from '../../context/LocaleContext'
import Money from '../../components/admin/Money'

const inputCls = 'border border-gray-300 rounded px-2 py-1.5 text-sm'

function InventoryTableRow({ row, warehouseName, onSave }) {
  const { t } = useLocale()
  const [form, setForm] = useState({ stock: row.stock, incoming: row.incoming, min_stock: row.min_stock })
  const [saving, setSaving] = useState(false)
  const dirty = form.stock !== row.stock || form.incoming !== row.incoming || form.min_stock !== row.min_stock

  const update = (field) => (e) => setForm((f) => ({ ...f, [field]: Number(e.target.value) }))

  const save = async () => {
    setSaving(true)
    try {
      await onSave(form)
    } finally {
      setSaving(false)
    }
  }

  return (
    <tr>
      <td className="py-1">{warehouseName}</td>
      <td><input type="number" value={form.stock} onChange={update('stock')} className="w-16 border border-gray-200 rounded px-1 py-0.5 text-center" /></td>
      <td className="text-center text-gray-400">{row.reserved}</td>
      <td><input type="number" value={form.incoming} onChange={update('incoming')} className="w-16 border border-gray-200 rounded px-1 py-0.5 text-center" /></td>
      <td><input type="number" value={form.min_stock} onChange={update('min_stock')} className="w-16 border border-gray-200 rounded px-1 py-0.5 text-center" /></td>
      <td>
        {dirty && (
          <button type="button" onClick={save} disabled={saving} className="text-brand disabled:opacity-40">
            {saving ? t('admin.common.saving') : t('admin.common.save')}
          </button>
        )}
      </td>
    </tr>
  )
}

function InventoryRow({ sku, warehouses, onProductChanged }) {
  const { t } = useLocale()
  const [rows, setRows] = useState(null)
  const [error, setError] = useState(null)
  const [addWarehouseId, setAddWarehouseId] = useState('')

  const load = () => adminListInventory(sku.id).then(setRows).catch((err) => setError(errorMessage(err, t('admin.productDetail.inventoryLoadFailed'))))
  useEffect(() => { load() }, [sku.id]) // eslint-disable-line react-hooks/exhaustive-deps

  if (error) return <p className="text-red-600 text-xs">{error}</p>
  if (!rows) return <p className="text-xs text-gray-400">{t('admin.common.loading')}</p>

  const usedWarehouseIds = new Set(rows.map((r) => r.warehouse_id))
  const availableWarehouses = warehouses.filter((w) => !usedWarehouseIds.has(w.id))

  // Reloads both this row's own data (reserved/etc.) and the parent product
  // (whose SKU.available_quantity summary would otherwise go stale).
  const saveRow = async (warehouseId, form) => {
    try {
      await adminUpdateInventory(sku.id, warehouseId, form)
      await load()
      await onProductChanged()
    } catch (err) {
      setError(errorMessage(err, t('admin.productDetail.inventorySaveFailed')))
    }
  }

  const addWarehouse = async () => {
    if (!addWarehouseId) return
    try {
      await adminAddInventory(sku.id, { warehouse_id: Number(addWarehouseId), stock: 0, incoming: 0, min_stock: 0 })
      setAddWarehouseId('')
      await load()
      await onProductChanged()
    } catch (err) {
      setError(errorMessage(err, t('admin.productDetail.warehouseAddFailed')))
    }
  }

  return (
    <div className="mt-2 pl-4 border-l-2 border-gray-100">
      <table className="text-xs w-full">
        <thead className="text-gray-500">
          <tr>
            <th className="text-left font-normal">{t('admin.productDetail.warehouse')}</th>
            <th className="font-normal">{t('admin.productDetail.stock')}</th>
            <th className="font-normal">{t('admin.productDetail.reserved')}</th>
            <th className="font-normal">{t('admin.productDetail.incoming')}</th>
            <th className="font-normal">{t('admin.productDetail.min')}</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <InventoryTableRow
              key={r.warehouse_id}
              row={r}
              warehouseName={warehouses.find((wh) => wh.id === r.warehouse_id)?.name ?? `#${r.warehouse_id}`}
              onSave={(form) => saveRow(r.warehouse_id, form)}
            />
          ))}
        </tbody>
      </table>
      {error && <p className="text-red-600 text-xs mt-1">{error}</p>}
      {availableWarehouses.length > 0 && (
        <div className="flex gap-2 mt-2">
          <select value={addWarehouseId} onChange={(e) => setAddWarehouseId(e.target.value)} className="border border-gray-300 rounded px-2 py-1 text-xs">
            <option value="">{t('admin.productDetail.addWarehousePrompt')}</option>
            {availableWarehouses.map((w) => <option key={w.id} value={w.id}>{w.name}</option>)}
          </select>
          <button onClick={addWarehouse} className="text-xs text-brand">{t('admin.productDetail.add')}</button>
        </div>
      )}
    </div>
  )
}

function SkuBlock({ sku, warehouses, onChanged }) {
  const { t } = useLocale()
  const [expanded, setExpanded] = useState(false)
  const [form, setForm] = useState({
    barcode: sku.barcode || '', retail_price: sku.retail_price, wholesale_price: sku.wholesale_price ?? '',
    distributor_price: sku.distributor_price ?? '', export_price: sku.export_price ?? '', special_price: sku.special_price ?? '',
    currency: sku.currency, is_active: sku.is_active,
  })
  const [error, setError] = useState(null)
  const [saving, setSaving] = useState(false)

  const update = (field) => (e) => {
    const value = e.target.type === 'checkbox' ? e.target.checked : e.target.value
    setForm((f) => ({ ...f, [field]: value }))
  }

  const save = async (e) => {
    e.preventDefault()
    setError(null)
    setSaving(true)
    try {
      const payload = {
        barcode: form.barcode || null,
        retail_price: Number(form.retail_price),
        wholesale_price: form.wholesale_price === '' ? null : Number(form.wholesale_price),
        distributor_price: form.distributor_price === '' ? null : Number(form.distributor_price),
        export_price: form.export_price === '' ? null : Number(form.export_price),
        special_price: form.special_price === '' ? null : Number(form.special_price),
        currency: form.currency,
        is_active: form.is_active,
      }
      await adminUpdateSku(sku.id, payload)
      await onChanged()
    } catch (err) {
      setError(errorMessage(err, t('admin.productDetail.skuSaveFailed')))
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="border border-gray-100 rounded p-3 mb-2">
      <button onClick={() => setExpanded((x) => !x)} className="text-sm font-medium w-full text-left flex justify-between">
        <span>{sku.sku_code} — <Money amount={sku.retail_price} currency={sku.currency} /> ({t('admin.productDetail.available', { n: sku.available_quantity })})</span>
        <span className="text-gray-400">{expanded ? '−' : '+'}</span>
      </button>
      {expanded && (
        <>
          <form onSubmit={save} className="grid grid-cols-3 gap-2 mt-3">
            <input placeholder={t('admin.productDetail.barcode')} value={form.barcode} onChange={update('barcode')} className={inputCls} />
            <input type="number" step="0.01" min="0.01" required placeholder={t('admin.productDetail.retailPrice')} value={form.retail_price} onChange={update('retail_price')} className={inputCls} />
            <input placeholder={t('admin.productDetail.currency')} maxLength={3} value={form.currency} onChange={update('currency')} className={inputCls} />
            <input type="number" step="0.01" placeholder={t('admin.productDetail.wholesalePrice')} value={form.wholesale_price} onChange={update('wholesale_price')} className={inputCls} />
            <input type="number" step="0.01" placeholder={t('admin.productDetail.distributorPrice')} value={form.distributor_price} onChange={update('distributor_price')} className={inputCls} />
            <input type="number" step="0.01" placeholder={t('admin.productDetail.exportPrice')} value={form.export_price} onChange={update('export_price')} className={inputCls} />
            <input type="number" step="0.01" placeholder={t('admin.productDetail.specialPrice')} value={form.special_price} onChange={update('special_price')} className={inputCls} />
            <label className="flex items-center gap-1 text-sm"><input type="checkbox" checked={form.is_active} onChange={update('is_active')} /> {t('admin.common.active')}</label>
            <button type="submit" disabled={saving} className="bg-brand text-white rounded px-3 py-1.5 text-sm disabled:opacity-40">{saving ? t('admin.common.saving') : t('admin.productDetail.saveSku')}</button>
          </form>
          {error && <p className="text-red-600 text-xs mt-1">{error}</p>}
          <InventoryRow sku={sku} warehouses={warehouses} onProductChanged={onChanged} />
        </>
      )}
    </div>
  )
}

function VariantBlock({ variant, warehouses, onChanged }) {
  const { t } = useLocale()
  const [expanded, setExpanded] = useState(false)
  const [form, setForm] = useState({ name: variant.name, color: variant.color, color_hex: variant.color_hex || '', photo_url: variant.photo_url || '', is_active: variant.is_active })
  const [error, setError] = useState(null)
  const [saving, setSaving] = useState(false)
  const [skuForm, setSkuForm] = useState({ sku_code: '', retail_price: '', currency: 'USD' })
  const [skuError, setSkuError] = useState(null)
  const [skuOpen, setSkuOpen] = useState(false)

  const update = (field) => (e) => {
    const value = e.target.type === 'checkbox' ? e.target.checked : e.target.value
    setForm((f) => ({ ...f, [field]: value }))
  }
  const updateSku = (field) => (e) => setSkuForm((f) => ({ ...f, [field]: e.target.value }))

  const save = async (e) => {
    e.preventDefault()
    setError(null)
    setSaving(true)
    try {
      await adminUpdateVariant(variant.id, { ...form, color_hex: form.color_hex || null, photo_url: form.photo_url || null })
      await onChanged()
    } catch (err) {
      setError(errorMessage(err, t('admin.productDetail.variantSaveFailed')))
    } finally {
      setSaving(false)
    }
  }

  const addSku = async (e) => {
    e.preventDefault()
    setSkuError(null)
    try {
      await adminCreateSku(variant.id, { sku_code: skuForm.sku_code, retail_price: Number(skuForm.retail_price), currency: skuForm.currency })
      setSkuForm({ sku_code: '', retail_price: '', currency: 'USD' })
      setSkuOpen(false)
      await onChanged()
    } catch (err) {
      setSkuError(errorMessage(err, t('admin.productDetail.skuAddFailed')))
    }
  }

  return (
    <div className="border border-gray-200 rounded-lg p-4 mb-3">
      <button onClick={() => setExpanded((x) => !x)} className="font-medium w-full text-left flex justify-between items-center">
        <span>{variant.name} ({variant.color}) {!variant.is_active && <span className="text-xs text-gray-400">{t('admin.common.no')}</span>}</span>
        <span className="text-gray-400">{expanded ? '−' : '+'}</span>
      </button>

      {expanded && (
        <>
          <form onSubmit={save} className="grid grid-cols-2 gap-2 mt-3 mb-4">
            <input placeholder={t('admin.common.name')} value={form.name} onChange={update('name')} className={inputCls} />
            <input placeholder={t('admin.productDetail.color')} value={form.color} onChange={update('color')} className={inputCls} />
            <input placeholder={t('admin.productDetail.colorHex')} value={form.color_hex} onChange={update('color_hex')} className={inputCls} />
            <input placeholder={t('admin.productDetail.photoUrl')} value={form.photo_url} onChange={update('photo_url')} className={inputCls} />
            <label className="flex items-center gap-1 text-sm"><input type="checkbox" checked={form.is_active} onChange={update('is_active')} /> {t('admin.common.active')}</label>
            <button type="submit" disabled={saving} className="bg-brand text-white rounded px-3 py-1.5 text-sm disabled:opacity-40 justify-self-start">{saving ? t('admin.common.saving') : t('admin.productDetail.saveVariant')}</button>
          </form>
          {error && <p className="text-red-600 text-xs mb-2">{error}</p>}

          <p className="text-xs font-semibold text-gray-500 uppercase mb-2">{t('admin.productDetail.skus')}</p>
          {variant.skus.map((sku) => <SkuBlock key={sku.id} sku={sku} warehouses={warehouses} onChanged={onChanged} />)}

          {skuOpen ? (
            <form onSubmit={addSku} className="grid grid-cols-3 gap-2 mt-2 border border-gray-100 rounded p-3">
              <input required placeholder={t('admin.productDetail.skuCode')} value={skuForm.sku_code} onChange={updateSku('sku_code')} className={inputCls} />
              <input required type="number" step="0.01" min="0.01" placeholder={t('admin.productDetail.retailPrice')} value={skuForm.retail_price} onChange={updateSku('retail_price')} className={inputCls} />
              <input placeholder={t('admin.productDetail.currency')} maxLength={3} value={skuForm.currency} onChange={updateSku('currency')} className={inputCls} />
              {skuError && <p className="text-red-600 text-xs col-span-3">{skuError}</p>}
              <button type="submit" className="bg-brand text-white rounded px-3 py-1.5 text-sm col-span-1">{t('admin.productDetail.addSku')}</button>
              <button type="button" onClick={() => setSkuOpen(false)} className="border border-gray-300 rounded px-3 py-1.5 text-sm col-span-1">{t('admin.common.cancel')}</button>
            </form>
          ) : (
            <button onClick={() => setSkuOpen(true)} className="text-sm text-brand mt-2">{t('admin.productDetail.addSku')}</button>
          )}
        </>
      )}
    </div>
  )
}

export default function AdminProductDetail() {
  const { t } = useLocale()
  const { productId } = useParams()
  const [product, setProduct] = useState(null)
  const [warehouses, setWarehouses] = useState([])
  const [error, setError] = useState(null)
  const [form, setForm] = useState(null)
  const [saving, setSaving] = useState(false)
  const [saveError, setSaveError] = useState(null)

  const [variantForm, setVariantForm] = useState({ name: '', color: '', color_hex: '' })
  const [variantOpen, setVariantOpen] = useState(false)
  const [variantError, setVariantError] = useState(null)

  const load = () => adminGetProduct(productId).then((p) => {
    setProduct(p)
    setForm({
      name: p.name, slug: p.slug, volume_ml: p.volume_ml, shape: p.shape || '', purpose: p.purpose || '',
      description: p.description || '', country_of_origin: p.country_of_origin || '', min_order_quantity: p.min_order_quantity,
    })
  }).catch((err) => setError(errorMessage(err, t('admin.productDetail.loadFailed'))))

  useEffect(() => {
    load()
    adminListWarehouses().then(setWarehouses).catch(() => {})
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [productId])

  if (error) return <p className="text-red-600 text-sm">{error}</p>
  if (!product || !form) return <p>{t('admin.common.loading')}</p>

  const update = (field) => (e) => setForm((f) => ({ ...f, [field]: e.target.value }))

  const saveProduct = async (e) => {
    e.preventDefault()
    setSaveError(null)
    setSaving(true)
    try {
      const payload = { ...form, volume_ml: Number(form.volume_ml), min_order_quantity: Number(form.min_order_quantity) }
      await adminUpdateProduct(product.id, payload)
      await load()
    } catch (err) {
      setSaveError(errorMessage(err, t('admin.productDetail.saveFailed')))
    } finally {
      setSaving(false)
    }
  }

  const addVariant = async (e) => {
    e.preventDefault()
    setVariantError(null)
    try {
      await adminCreateVariant(product.id, { ...variantForm, color_hex: variantForm.color_hex || null })
      setVariantForm({ name: '', color: '', color_hex: '' })
      setVariantOpen(false)
      await load()
    } catch (err) {
      setVariantError(errorMessage(err, t('admin.productDetail.variantAddFailed')))
    }
  }

  return (
    <div>
      <Link to="/admin/products" className="text-sm text-brand">&larr; {t('admin.productDetail.back')}</Link>
      <h1 className="text-2xl font-bold mt-2 mb-6">{product.name}</h1>

      <form onSubmit={saveProduct} className="border border-gray-200 rounded-lg p-4 mb-8 grid grid-cols-2 gap-3">
        <input required placeholder={t('admin.common.name')} value={form.name} onChange={update('name')} className={inputCls} />
        <input required placeholder={t('admin.common.slug')} value={form.slug} onChange={update('slug')} className={inputCls} />
        <input required type="number" min="1" placeholder={t('admin.products.volumeMl')} value={form.volume_ml} onChange={update('volume_ml')} className={inputCls} />
        <input type="number" min="1" placeholder={t('admin.products.minOrderQty')} value={form.min_order_quantity} onChange={update('min_order_quantity')} className={inputCls} />
        <input placeholder={t('admin.products.shape')} value={form.shape} onChange={update('shape')} className={inputCls} />
        <input placeholder={t('admin.products.purpose')} value={form.purpose} onChange={update('purpose')} className={inputCls} />
        <input placeholder={t('admin.products.countryOfOrigin')} value={form.country_of_origin} onChange={update('country_of_origin')} className={`${inputCls} col-span-2`} />
        <textarea placeholder={t('admin.products.description')} value={form.description} onChange={update('description')} rows={3} className={`${inputCls} col-span-2`} />
        {saveError && <p className="text-red-600 text-sm col-span-2">{saveError}</p>}
        <button type="submit" disabled={saving} className="bg-brand text-white rounded px-4 py-2 text-sm font-medium disabled:opacity-40 justify-self-start">
          {saving ? t('admin.common.saving') : t('admin.productDetail.saveProduct')}
        </button>
      </form>

      <div className="flex items-center justify-between mb-3">
        <h2 className="text-lg font-semibold">{t('admin.productDetail.variants')}</h2>
        {!variantOpen && <button onClick={() => setVariantOpen(true)} className="text-sm text-brand">{t('admin.productDetail.addVariant')}</button>}
      </div>

      {variantOpen && (
        <form onSubmit={addVariant} className="grid grid-cols-3 gap-2 border border-gray-200 rounded-lg p-4 mb-4">
          <input required placeholder={t('admin.common.name')} value={variantForm.name} onChange={(e) => setVariantForm((f) => ({ ...f, name: e.target.value }))} className={inputCls} />
          <input required placeholder={t('admin.productDetail.color')} value={variantForm.color} onChange={(e) => setVariantForm((f) => ({ ...f, color: e.target.value }))} className={inputCls} />
          <input placeholder={t('admin.productDetail.colorHex')} value={variantForm.color_hex} onChange={(e) => setVariantForm((f) => ({ ...f, color_hex: e.target.value }))} className={inputCls} />
          {variantError && <p className="text-red-600 text-xs col-span-3">{variantError}</p>}
          <button type="submit" className="bg-brand text-white rounded px-3 py-1.5 text-sm">{t('admin.productDetail.add')}</button>
          <button type="button" onClick={() => setVariantOpen(false)} className="border border-gray-300 rounded px-3 py-1.5 text-sm">{t('admin.common.cancel')}</button>
        </form>
      )}

      {product.variants.map((v) => (
        <VariantBlock key={v.id} variant={v} warehouses={warehouses} onChanged={load} />
      ))}
      {product.variants.length === 0 && <p className="text-gray-400 text-sm">{t('admin.productDetail.noVariants')}</p>}
    </div>
  )
}
