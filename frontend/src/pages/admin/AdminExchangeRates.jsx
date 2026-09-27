import { useEffect, useState } from 'react'
import { adminCreateExchangeRate, adminListExchangeRates, adminSyncExchangeRates, adminUpdateExchangeRate } from '../../api/admin'
import { errorMessage } from '../../api/client'
import { useLocale } from '../../context/LocaleContext'

export default function AdminExchangeRates() {
  const { t } = useLocale()
  const [rates, setRates] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [syncing, setSyncing] = useState(false)
  const [syncMessage, setSyncMessage] = useState(null)

  const [newForm, setNewForm] = useState({ currency: '', units_per_usd: '' })
  const [newOpen, setNewOpen] = useState(false)
  const [newError, setNewError] = useState(null)

  const load = () => adminListExchangeRates().then(setRates).catch((err) => setError(errorMessage(err, t('admin.exchangeRates.loadFailed')))).finally(() => setLoading(false))
  useEffect(() => { load() }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const handleSync = async () => {
    setSyncMessage(null)
    setSyncing(true)
    try {
      await adminSyncExchangeRates()
      setSyncMessage(t('admin.exchangeRates.synced'))
      await load()
    } catch (err) {
      setSyncMessage(errorMessage(err, t('admin.exchangeRates.syncFailed')))
    } finally {
      setSyncing(false)
    }
  }

  const updateRate = async (id, unitsPerUsd) => {
    try {
      await adminUpdateExchangeRate(id, Number(unitsPerUsd))
      await load()
    } catch (err) {
      setError(errorMessage(err, t('admin.exchangeRates.updateFailed')))
    }
  }

  const addRate = async (e) => {
    e.preventDefault()
    setNewError(null)
    try {
      await adminCreateExchangeRate({ currency: newForm.currency, units_per_usd: Number(newForm.units_per_usd) })
      setNewForm({ currency: '', units_per_usd: '' })
      setNewOpen(false)
      await load()
    } catch (err) {
      setNewError(errorMessage(err, t('admin.exchangeRates.addFailed')))
    }
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-2xl font-bold">{t('admin.exchangeRates.title')}</h1>
        <div className="flex gap-2">
          {!newOpen && <button onClick={() => setNewOpen(true)} className="border border-gray-300 rounded px-4 py-2 text-sm">{t('admin.exchangeRates.addCurrency')}</button>}
          <button onClick={handleSync} disabled={syncing} className="bg-brand text-white px-4 py-2 rounded text-sm font-medium disabled:opacity-40">
            {syncing ? t('admin.exchangeRates.syncing') : t('admin.exchangeRates.sync')}
          </button>
        </div>
      </div>

      {syncMessage && <p className="text-sm mb-3">{syncMessage}</p>}
      {loading && <p>{t('admin.common.loading')}</p>}
      {error && <p className="text-red-600 text-sm mb-3">{error}</p>}

      {newOpen && (
        <form onSubmit={addRate} className="border border-gray-200 rounded-lg p-4 mb-6 flex gap-2 items-start">
          <input required placeholder={t('admin.exchangeRates.currency')} maxLength={3} value={newForm.currency} onChange={(e) => setNewForm((f) => ({ ...f, currency: e.target.value.toUpperCase() }))} className="border border-gray-300 rounded px-3 py-2 text-sm" />
          <input required type="number" step="0.0001" min="0" placeholder={t('admin.exchangeRates.unitsPerUsd')} value={newForm.units_per_usd} onChange={(e) => setNewForm((f) => ({ ...f, units_per_usd: e.target.value }))} className="border border-gray-300 rounded px-3 py-2 text-sm" />
          <button type="submit" className="bg-brand text-white px-4 py-2 rounded text-sm">{t('admin.productDetail.add')}</button>
          <button type="button" onClick={() => setNewOpen(false)} className="border border-gray-300 rounded px-4 py-2 text-sm">{t('admin.common.cancel')}</button>
          {newError && <p className="text-red-600 text-sm">{newError}</p>}
        </form>
      )}

      {!loading && (
        <div className="border border-gray-200 rounded-lg overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-left"><tr><th className="px-3 py-2">{t('admin.common.name')}</th><th className="px-3 py-2">{t('admin.exchangeRates.unitsPerUsd')}</th></tr></thead>
            <tbody className="divide-y divide-gray-100">
              {rates.map((r) => (
                <tr key={r.id}>
                  <td className="px-3 py-2 font-medium">{r.currency}</td>
                  <td className="px-3 py-2">
                    <input type="number" step="0.0001" defaultValue={r.units_per_usd} onBlur={(e) => updateRate(r.id, e.target.value)} className="w-32 border border-gray-200 rounded px-2 py-1" />
                  </td>
                </tr>
              ))}
              {rates.length === 0 && <tr><td colSpan={2} className="px-3 py-6 text-center text-gray-400">{t('admin.exchangeRates.none')}</td></tr>}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
