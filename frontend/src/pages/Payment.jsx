import { useEffect, useState } from 'react'
import { useLocale } from '../context/LocaleContext'
import { getPaymentMethods } from '../api/orders'
import { listPageSections } from '../api/pageSections'
import Seo from '../components/Seo'
import { useShipCountry } from '../lib/shipCountry'

export default function Payment() {
  const { t, locale } = useLocale()
  const country = useShipCountry()
  const [methods, setMethods] = useState([])
  const [sections, setSections] = useState([])

  // Methods that do not work for the chosen delivery country are not listed.
  useEffect(() => {
    getPaymentMethods(country || undefined).then(setMethods).catch(() => {})
  }, [country])

  useEffect(() => {
    listPageSections('payment', locale).then(setSections).catch(() => {})
  }, [locale])

  const enabled = methods.filter((m) => m.enabled)

  return (
    <div className="max-w-2xl mx-auto px-4 py-10">
      <Seo title={t('payment.title')} />
      <h1 className="text-3xl font-bold mb-3">{t('payment.title')}</h1>
      <p className="text-gray-600 mb-2">{t('payment.subtitle')}</p>
      <p className="text-sm text-gray-500 mb-6">{country ? t('payment.forCountry', { country }) : t('payment.chooseCountry')}</p>

      {enabled.length > 0 ? (
        <ul className="space-y-3">
          {enabled.map((m) => (
            <li key={m.id} className="border border-gray-200 rounded-lg p-4 flex items-center justify-between">
              <span className="font-medium">{m.display_name}</span>
              <span className="text-xs text-green-700">{t('payment.available')}</span>
            </li>
          ))}
        </ul>
      ) : (
        <p className="text-sm text-gray-500">{t('payment.noneAvailable')}</p>
      )}

      <div className="mt-8 space-y-4">
        {sections.map((s) => (
          <div key={s.id}>
            <h2 className="font-semibold mb-1">{s.title}</h2>
            <p className="text-sm text-gray-500">{s.body}</p>
          </div>
        ))}
      </div>
    </div>
  )
}
