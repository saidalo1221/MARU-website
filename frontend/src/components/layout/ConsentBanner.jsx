import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { onOpenConsentSettings, setConsent, useConsent } from '../../lib/consent'
import { useLocale } from '../../context/LocaleContext'

// Asks for optional-tracking consent until the visitor chooses, and again
// whenever the footer's "Cookie settings" link is used. Declining is as easy as
// accepting, and all checkboxes start unticked.
export default function ConsentBanner() {
  const { t } = useLocale()
  const consent = useConsent()
  const [reopened, setReopened] = useState(false)
  const [analytics, setAnalytics] = useState(false)
  const [ads, setAds] = useState(false)
  const [geo, setGeo] = useState(false)

  useEffect(
    () =>
      onOpenConsentSettings(() => {
        setAnalytics(consent?.analytics === true)
        setAds(consent?.ads === true)
        setGeo(consent?.geo === true)
        setReopened(true)
      }),
    [consent]
  )

  if (consent && !reopened) return null

  const choose = (choice) => {
    setConsent(choice)
    setReopened(false)
  }

  return (
    <section
      aria-label={t('consent.title')}
      className="fixed bottom-0 inset-x-0 z-[60] bg-white border-t border-gray-300 shadow-lg p-4 text-sm"
    >
      <div className="max-w-4xl mx-auto">
        <p className="font-semibold mb-1">{t('consent.title')}</p>
        <p className="text-gray-600 mb-3">
          {t('consent.text')}{' '}
          <Link to="/privacy" className="underline">{t('consent.policyLink')}</Link>
        </p>
        <div className="flex flex-col sm:flex-row sm:flex-wrap gap-2 sm:gap-6 mb-3">
          <label className="flex items-start gap-2">
            <input type="checkbox" checked={analytics} onChange={(e) => setAnalytics(e.target.checked)} className="mt-1" />
            <span>{t('consent.analytics')}</span>
          </label>
          <label className="flex items-start gap-2">
            <input type="checkbox" checked={ads} onChange={(e) => setAds(e.target.checked)} className="mt-1" />
            <span>{t('consent.ads')}</span>
          </label>
          <label className="flex items-start gap-2">
            <input type="checkbox" checked={geo} onChange={(e) => setGeo(e.target.checked)} className="mt-1" />
            <span>{t('consent.geo')}</span>
          </label>
        </div>
        <div className="flex flex-wrap gap-2">
          <button onClick={() => choose({ analytics: true, ads: true, geo: true })} className="bg-brand text-white rounded px-4 py-2 font-medium">
            {t('consent.acceptAll')}
          </button>
          <button onClick={() => choose({ analytics: false, ads: false, geo: false })} className="border border-brand text-brand rounded px-4 py-2 font-medium">
            {t('consent.essentialOnly')}
          </button>
          <button onClick={() => choose({ analytics, ads, geo })} className="border border-gray-300 rounded px-4 py-2">
            {t('consent.save')}
          </button>
        </div>
      </div>
    </section>
  )
}
