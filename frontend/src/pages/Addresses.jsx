import { useEffect, useState } from 'react'
import { Navigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { useLocale } from '../context/LocaleContext'
import { listShippingCountries } from '../api/shipping'
import { createAddress, deleteAddress, listAddresses, updateAddress } from '../api/addresses'
import { errorMessage } from '../api/client'
import AccountNav from '../components/account/AccountNav'
import MapPicker from '../components/MapPicker'
import Seo from '../components/Seo'

const emptyForm = {
  label: '',
  first_name: '',
  last_name: '',
  phone: '',
  country: '',
  region: '',
  city: '',
  address_line: '',
  postal_code: '',
  is_default: false,
  latitude: null,
  longitude: null,
}

export default function Addresses() {
  const { user, loading: authLoading } = useAuth()
  const { t } = useLocale()
  const [addresses, setAddresses] = useState([])
  const [countries, setCountries] = useState([])
  const [loading, setLoading] = useState(true)
  const [editingId, setEditingId] = useState(null)
  const [form, setForm] = useState(emptyForm)
  const [formOpen, setFormOpen] = useState(false)
  const [error, setError] = useState(null)
  const [submitting, setSubmitting] = useState(false)

  const load = () => listAddresses().then(setAddresses).finally(() => setLoading(false))

  useEffect(() => {
    if (!user) return
    load()
    listShippingCountries().then(setCountries).catch(() => {})
  }, [user])

  if (authLoading) return null
  if (!user) return <Navigate to="/login" replace />

  const update = (field) => (e) => {
    const value = e.target.type === 'checkbox' ? e.target.checked : e.target.value
    setForm((f) => ({ ...f, [field]: value }))
  }

  const openNew = () => {
    setEditingId(null)
    setForm(emptyForm)
    setError(null)
    setFormOpen(true)
  }

  const openEdit = (address) => {
    setEditingId(address.id)
    setForm({ ...emptyForm, ...address, region: address.region || '' })
    setError(null)
    setFormOpen(true)
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      if (editingId) {
        await updateAddress(editingId, form)
      } else {
        await createAddress(form)
      }
      setFormOpen(false)
      await load()
    } catch (err) {
      setError(errorMessage(err, t('addresses.saveFailed')))
    } finally {
      setSubmitting(false)
    }
  }

  const handleDelete = async (id) => {
    await deleteAddress(id)
    await load()
  }

  return (
    <div className="max-w-2xl mx-auto px-4 py-8">
      <Seo title={t('addresses.title')} noindex />
      <AccountNav />
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-3xl font-semibold tracking-tight md:text-4xl">{t('addresses.title')}</h1>
        {!formOpen && (
          <button onClick={openNew} className="rounded-full bg-brand px-6 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-brand-dark disabled:opacity-40">
            {t('addresses.add')}
          </button>
        )}
      </div>

      {loading && <p>{t('addresses.loading')}</p>}

      {formOpen && (
        <form onSubmit={handleSubmit} className="mb-6 space-y-4 rounded-3xl border border-gray-200 bg-gray-50 p-6">
          <div className="grid grid-cols-2 gap-3">
            <input placeholder={t('addresses.label')} aria-label={t('addresses.label')} value={form.label || ''} onChange={update('label')} className="rounded-2xl border border-gray-300 bg-white px-4 py-2.5 text-sm col-span-2" />
            <input required placeholder={t('checkout.firstName')} aria-label={t('checkout.firstName')} value={form.first_name} onChange={update('first_name')} className="rounded-2xl border border-gray-300 bg-white px-4 py-2.5 text-sm" />
            <input required placeholder={t('checkout.lastName')} aria-label={t('checkout.lastName')} value={form.last_name} onChange={update('last_name')} className="rounded-2xl border border-gray-300 bg-white px-4 py-2.5 text-sm" />
            <input required type="tel" placeholder={t('checkout.phone')} aria-label={t('checkout.phone')} value={form.phone} onChange={update('phone')} className="rounded-2xl border border-gray-300 bg-white px-4 py-2.5 text-sm col-span-2" />
            <div className="col-span-2">
              <MapPicker
                latitude={form.latitude}
                longitude={form.longitude}
                onChange={({ latitude, longitude }) => setForm((f) => ({ ...f, latitude, longitude }))}
                onReverseGeocode={({ country, city, addressLine, postalCode }) => {
                  const matchedCountry = countries.find((c) => c.toLowerCase() === country.toLowerCase())
                  setForm((f) => ({
                    ...f,
                    country: matchedCountry || f.country,
                    city: city || f.city,
                    address_line: addressLine || f.address_line,
                    postal_code: postalCode || f.postal_code,
                  }))
                }}
              />
            </div>
            <select required aria-label={t('checkout.selectCountry')} value={form.country} onChange={update('country')} className="rounded-2xl border border-gray-300 bg-white px-4 py-2.5 text-sm col-span-2">
              <option value="">{t('checkout.selectCountry')}</option>
              {countries.map((c) => <option key={c} value={c}>{c}</option>)}
            </select>
            <input placeholder={t('checkout.region')} aria-label={t('checkout.region')} value={form.region} onChange={update('region')} className="rounded-2xl border border-gray-300 bg-white px-4 py-2.5 text-sm col-span-2" />
            <input required placeholder={t('checkout.city')} aria-label={t('checkout.city')} value={form.city} onChange={update('city')} className="rounded-2xl border border-gray-300 bg-white px-4 py-2.5 text-sm" />
            <input placeholder={t('checkout.postalCode')} aria-label={t('checkout.postalCode')} value={form.postal_code} onChange={update('postal_code')} className="rounded-2xl border border-gray-300 bg-white px-4 py-2.5 text-sm" />
            <input required placeholder={t('checkout.address')} aria-label={t('checkout.address')} value={form.address_line} onChange={update('address_line')} className="rounded-2xl border border-gray-300 bg-white px-4 py-2.5 text-sm col-span-2" />
          </div>
          <label className="flex items-center gap-2 text-sm">
            <input type="checkbox" checked={form.is_default} onChange={update('is_default')} />
            {t('addresses.setDefault')}
          </label>
          {error && <p role="alert" className="text-sm text-red-600">{error}</p>}
          <div className="flex gap-2">
            <button type="submit" disabled={submitting} className="rounded-full bg-brand px-6 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-brand-dark disabled:opacity-40">
              {submitting ? t('addresses.saving') : t('addresses.save')}
            </button>
            <button type="button" onClick={() => setFormOpen(false)} className="border border-gray-300 rounded px-4 py-2 text-sm">
              {t('addresses.cancel')}
            </button>
          </div>
        </form>
      )}

      {!loading && addresses.length === 0 && !formOpen && (
        <p className="rounded-3xl bg-brand-light px-6 py-14 text-center text-gray-700">{t('addresses.empty')}</p>
      )}

      <ul className="space-y-3">
        {addresses.map((a) => (
          <li key={a.id} className="flex items-start justify-between gap-4 rounded-3xl border border-gray-200 bg-gray-50 p-5">
            <div className="text-sm">
              {a.label && <p className="font-medium">{a.label}{a.is_default && ` · ${t('addresses.default')}`}</p>}
              {!a.label && a.is_default && <p className="font-medium">{t('addresses.default')}</p>}
              <p>{a.first_name} {a.last_name} · {a.phone}</p>
              <p className="text-gray-500">{a.address_line}, {a.city}{a.region ? `, ${a.region}` : ''}, {a.country} {a.postal_code}</p>
            </div>
            <div className="flex gap-3 text-sm">
              <button onClick={() => openEdit(a)} className="text-brand">{t('addresses.edit')}</button>
              <button onClick={() => handleDelete(a.id)} className="text-red-600">{t('cart.remove')}</button>
            </div>
          </li>
        ))}
      </ul>
    </div>
  )
}
