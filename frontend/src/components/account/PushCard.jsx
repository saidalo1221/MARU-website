import { useEffect, useState } from 'react'
import { useLocale } from '../../context/LocaleContext'
import { disablePush, enablePush, pushState } from '../../lib/push'

// Opt in / out of web push on this device. Hidden when the server has no push keys.
export default function PushCard() {
  const { t } = useLocale()
  const [state, setState] = useState(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)

  const refresh = () => pushState().then(setState).catch(() => setState('unavailable'))
  useEffect(() => { refresh() }, [])

  const toggle = async () => {
    setBusy(true)
    setError(null)
    try {
      if (state === 'on') await disablePush()
      else await enablePush()
    } catch (err) {
      if (err.message !== 'denied') setError(t('pushNotifications.failed'))
    } finally {
      await refresh()
      setBusy(false)
    }
  }

  if (!state || state === 'unavailable') return null
  return (
    <section className="rounded-3xl border border-gray-200 bg-gray-50 p-6" aria-labelledby="push-title">
      <h2 id="push-title" className="mb-1 text-lg font-semibold">{t('pushNotifications.title')}</h2>
      <p className="text-sm text-gray-500 mb-3">{t('pushNotifications.text')}</p>
      {state === 'unsupported' && <p className="text-sm text-gray-600">{t('pushNotifications.unsupported')}</p>}
      {state === 'denied' && <p className="text-sm text-gray-600">{t('pushNotifications.denied')}</p>}
      {(state === 'on' || state === 'off') && (
        <div className="flex items-center gap-3">
          <button type="button" onClick={toggle} disabled={busy} className="rounded-full border border-brand px-5 py-2 text-sm font-medium text-brand transition-colors hover:bg-brand-light disabled:opacity-40">
            {state === 'on' ? t('pushNotifications.disable') : t('pushNotifications.enable')}
          </button>
          {state === 'on' && <span role="status" className="text-sm text-green-700">{t('pushNotifications.on')}</span>}
        </div>
      )}
      {error && <p role="alert" className="text-sm text-red-600 mt-2">{error}</p>}
    </section>
  )
}
