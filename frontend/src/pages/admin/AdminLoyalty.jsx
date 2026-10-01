import { useEffect, useState } from 'react'
import { apiRequest, errorMessage } from '../../api/client'
import { useLocale } from '../../context/LocaleContext'

export default function AdminLoyalty() {
  const { t } = useLocale()
  const [settings, setSettings] = useState(null)
  const [msg, setMsg] = useState(null)
  const [error, setError] = useState(null)
  const [adjust, setAdjust] = useState({ user_id: '', points: '', note: '' })
  const [adjustMsg, setAdjustMsg] = useState(null)
  const [adjustError, setAdjustError] = useState(null)

  useEffect(() => {
    apiRequest('/admin/loyalty/settings').then(setSettings).catch((err) => setError(errorMessage(err, t('admin.loyalty.failed'))))
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const save = async (e) => {
    e.preventDefault()
    setError(null)
    setMsg(null)
    try {
      const saved = await apiRequest('/admin/loyalty/settings', {
        method: 'PUT',
        body: {
          enabled: settings.enabled,
          earn_per_usd: Number(settings.earn_per_usd),
          point_value_usd: Number(settings.point_value_usd),
          max_redeem_percent: Number(settings.max_redeem_percent),
        },
      })
      setSettings(saved)
      setMsg(t('admin.loyalty.saved'))
    } catch (err) {
      setError(errorMessage(err, t('admin.loyalty.failed')))
    }
  }

  const applyAdjust = async (e) => {
    e.preventDefault()
    setAdjustError(null)
    setAdjustMsg(null)
    try {
      const id = Number(adjust.user_id)
      await apiRequest('/admin/loyalty/adjust', { method: 'POST', body: { user_id: id, points: Number(adjust.points), note: adjust.note } })
      const now = await apiRequest(`/admin/loyalty/users/${id}`)
      setAdjustMsg(t('admin.loyalty.balanceNow', { id, balance: now.balance }))
      setAdjust({ user_id: '', points: '', note: '' })
    } catch (err) {
      setAdjustError(errorMessage(err, t('admin.loyalty.failed')))
    }
  }

  const cls = 'border border-gray-300 rounded px-3 py-2 text-sm'
  const set = (k) => (e) => setSettings((s) => ({ ...s, [k]: e.target.type === 'checkbox' ? e.target.checked : e.target.value }))

  return (
    <div>
      <h1 className="text-2xl font-bold mb-1">{t('admin.loyalty.title')}</h1>
      <p className="text-sm text-gray-500 mb-4">{t('admin.loyalty.subtitle')}</p>

      {settings && (
        <form onSubmit={save} className="border border-gray-200 rounded-lg p-4 mb-8 grid sm:grid-cols-2 gap-3">
          <label className="flex items-center gap-2 text-sm sm:col-span-2"><input type="checkbox" checked={!!settings.enabled} onChange={set('enabled')} /> {t('admin.loyalty.enabled')}</label>
          <label className="text-xs text-gray-500 flex flex-col gap-1">{t('admin.loyalty.earn')}
            <input type="number" min="0" step="0.01" required value={settings.earn_per_usd} onChange={set('earn_per_usd')} className={`${cls} text-gray-900`} />
          </label>
          <label className="text-xs text-gray-500 flex flex-col gap-1">{t('admin.loyalty.value')}
            <input type="number" min="0" step="0.0001" required value={settings.point_value_usd} onChange={set('point_value_usd')} className={`${cls} text-gray-900`} />
          </label>
          <label className="text-xs text-gray-500 flex flex-col gap-1">{t('admin.loyalty.percent')}
            <input type="number" min="0" max="100" step="1" required value={settings.max_redeem_percent} onChange={set('max_redeem_percent')} className={`${cls} text-gray-900`} />
          </label>
          {error && <p role="alert" className="text-sm text-red-600 sm:col-span-2">{error}</p>}
          {msg && <p role="status" className="text-sm text-green-700 sm:col-span-2">{msg}</p>}
          <button type="submit" className="bg-brand text-white rounded px-4 py-2 text-sm font-medium justify-self-start">{t('admin.loyalty.save')}</button>
        </form>
      )}

      <form onSubmit={applyAdjust} className="border border-gray-200 rounded-lg p-4 grid sm:grid-cols-3 gap-3">
        <h2 className="font-semibold sm:col-span-3">{t('admin.loyalty.adjustTitle')}</h2>
        <input required type="number" min="1" placeholder={t('admin.loyalty.userId')} aria-label={t('admin.loyalty.userId')} value={adjust.user_id} onChange={(e) => setAdjust((a) => ({ ...a, user_id: e.target.value }))} className={cls} />
        <input required type="number" step="1" placeholder={t('admin.loyalty.points')} aria-label={t('admin.loyalty.points')} value={adjust.points} onChange={(e) => setAdjust((a) => ({ ...a, points: e.target.value }))} className={cls} />
        <input required maxLength={300} placeholder={t('admin.loyalty.note')} aria-label={t('admin.loyalty.note')} value={adjust.note} onChange={(e) => setAdjust((a) => ({ ...a, note: e.target.value }))} className={cls} />
        {adjustError && <p role="alert" className="text-sm text-red-600 sm:col-span-3">{adjustError}</p>}
        {adjustMsg && <p role="status" className="text-sm text-green-700 sm:col-span-3">{adjustMsg}</p>}
        <button type="submit" className="border border-gray-300 rounded px-4 py-2 text-sm justify-self-start">{t('admin.loyalty.adjust')}</button>
      </form>
    </div>
  )
}
