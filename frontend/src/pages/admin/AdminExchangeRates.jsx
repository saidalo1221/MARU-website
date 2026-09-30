import { useEffect, useMemo, useRef, useState } from 'react'
import {
  adminCreateExchangeRate,
  adminDeleteExchangeRate,
  adminListAvailableCurrencies,
  adminListExchangeRates,
  adminSyncExchangeRates,
  adminUpdateExchangeRate,
} from '../../api/admin'
import { errorMessage } from '../../api/client'
import { useLocale } from '../../context/LocaleContext'

const MAX_SUGGESTIONS = 8

// Type-to-filter picker over the FX provider's currency list, same
// interaction shape as the storefront's product SearchBar — search box +
// dropdown of matches, click to select.
function CurrencyPicker({ onSelect }) {
  const { t } = useLocale()
  const [all, setAll] = useState([])
  const [loadError, setLoadError] = useState(null)
  const [query, setQuery] = useState('')
  const [open, setOpen] = useState(false)
  const containerRef = useRef(null)

  useEffect(() => {
    adminListAvailableCurrencies()
      .then(setAll)
      .catch((err) => setLoadError(errorMessage(err, t('admin.exchangeRates.currenciesLoadFailed'))))
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    const onClickOutside = (e) => {
      if (containerRef.current && !containerRef.current.contains(e.target)) setOpen(false)
    }
    document.addEventListener('mousedown', onClickOutside)
    return () => document.removeEventListener('mousedown', onClickOutside)
  }, [])

  const suggestions = useMemo(() => {
    const q = query.trim().toLowerCase()
    if (!q) return []
    return all
      .filter((c) => c.code.toLowerCase().includes(q) || c.name.toLowerCase().includes(q))
      .slice(0, MAX_SUGGESTIONS)
  }, [all, query])

  return (
    <div ref={containerRef} className="relative">
      <input
        placeholder={t('admin.exchangeRates.searchCurrency')} aria-label={t('admin.exchangeRates.searchCurrency')}
        value={query}
        onChange={(e) => { setQuery(e.target.value); setOpen(true) }}
        onFocus={() => setOpen(true)}
        className="border border-gray-300 rounded px-3 py-2 text-sm w-64"
      />
      {loadError && <p role="alert" className="text-xs text-red-600 mt-1">{loadError}</p>}
      {open && suggestions.length > 0 && (
        <ul className="absolute top-full left-0 right-0 mt-1 bg-white border border-gray-200 rounded shadow-lg z-50 overflow-hidden max-h-64 overflow-y-auto">
          {suggestions.map((c) => (
            <li key={c.code}>
              <button
                type="button"
                onClick={() => { onSelect(c); setQuery(''); setOpen(false) }}
                className="w-full text-left px-3 py-2 text-sm hover:bg-gray-50"
              >
                <span className="font-medium">{c.code}</span> — {c.name}
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

export default function AdminExchangeRates() {
  const { t } = useLocale()
  const [rates, setRates] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [syncing, setSyncing] = useState(false)
  const [syncMessage, setSyncMessage] = useState(null)

  const [selectedCurrency, setSelectedCurrency] = useState(null)
  const [newOpen, setNewOpen] = useState(false)
  const [newError, setNewError] = useState(null)
  const [adding, setAdding] = useState(false)
  const [manualRate, setManualRate] = useState('')

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

  const deleteRate = async (id) => {
    try {
      await adminDeleteExchangeRate(id)
      await load()
    } catch (err) {
      setError(errorMessage(err, t('admin.exchangeRates.deleteFailed')))
    }
  }

  const addCurrency = async (currency, rate) => {
    setNewError(null)
    setAdding(true)
    try {
      const payload = rate ? { currency, units_per_usd: Number(rate) } : { currency }
      await adminCreateExchangeRate(payload)
      setSelectedCurrency(null)
      setManualRate('')
      setNewOpen(false)
      await load()
    } catch (err) {
      setNewError(errorMessage(err, t('admin.exchangeRates.addFailed')))
    } finally {
      setAdding(false)
    }
  }

  const handlePickCurrency = (currency) => {
    setSelectedCurrency(currency)
    addCurrency(currency.code)
  }

  const handleManualSave = (e) => {
    e.preventDefault()
    if (selectedCurrency) addCurrency(selectedCurrency.code, manualRate)
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
      {error && <p role="alert" className="text-red-600 text-sm mb-3">{error}</p>}

      {newOpen && (
        <div className="border border-gray-200 rounded-lg p-4 mb-6">
          <div className="flex gap-2 items-start">
            <CurrencyPicker onSelect={handlePickCurrency} />
            <button
              type="button"
              onClick={() => { setNewOpen(false); setSelectedCurrency(null); setNewError(null) }}
              className="border border-gray-300 rounded px-4 py-2 text-sm"
            >
              {t('admin.common.cancel')}
            </button>
          </div>
          <p className="text-xs text-gray-500 mt-2">{t('admin.exchangeRates.autoRateHint')}</p>
          {adding && <p className="text-sm mt-2">{t('admin.exchangeRates.fetchingRate')}</p>}
          {newError && (
            <div className="mt-3">
              <p role="alert" className="text-red-600 text-sm mb-2">{newError}</p>
              {selectedCurrency && (
                <form onSubmit={handleManualSave} className="flex gap-2 items-start">
                  <input
                    required
                    type="number"
                    step="0.0001"
                    min="0"
                    placeholder={t('admin.exchangeRates.unitsPerUsd')} aria-label={t('admin.exchangeRates.unitsPerUsd')}
                    value={manualRate}
                    onChange={(e) => setManualRate(e.target.value)}
                    className="border border-gray-300 rounded px-3 py-2 text-sm"
                  />
                  <button type="submit" className="bg-brand text-white px-4 py-2 rounded text-sm">
                    {t('admin.exchangeRates.saveManualRate', { currency: selectedCurrency.code })}
                  </button>
                </form>
              )}
            </div>
          )}
        </div>
      )}

      {!loading && (
        <div className="border border-gray-200 rounded-lg overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-left"><tr><th className="px-3 py-2">{t('admin.common.name')}</th><th className="px-3 py-2">{t('admin.exchangeRates.unitsPerUsd')}</th><th className="px-3 py-2"></th></tr></thead>
            <tbody className="divide-y divide-gray-100">
              {rates.map((r) => (
                <tr key={r.id}>
                  <td className="px-3 py-2 font-medium">{r.currency}</td>
                  <td className="px-3 py-2">
                    <input type="number" step="0.0001" defaultValue={r.units_per_usd} aria-label={t('admin.exchangeRates.unitsPerUsd')} onBlur={(e) => updateRate(r.id, e.target.value)} className="w-32 border border-gray-200 rounded px-2 py-1" />
                  </td>
                  <td className="px-3 py-2 text-right">
                    <button type="button" onClick={() => deleteRate(r.id)} className="text-red-600 text-xs">{t('admin.common.delete')}</button>
                  </td>
                </tr>
              ))}
              {rates.length === 0 && <tr><td colSpan={3} className="px-3 py-6 text-center text-gray-400">{t('admin.exchangeRates.none')}</td></tr>}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
