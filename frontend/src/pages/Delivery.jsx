import { useEffect, useState } from 'react'
import { useLocale } from '../context/LocaleContext'
import { listShippingCountries, listShippingMethods } from '../api/shipping'

const UZBEKISTAN = 'Uzbekistan'

export default function Delivery() {
  const { t } = useLocale()
  const [countries, setCountries] = useState([])
  const [domesticMethods, setDomesticMethods] = useState([])
  const [internationalCountries, setInternationalCountries] = useState([])

  useEffect(() => {
    listShippingCountries().then(async (list) => {
      setCountries(list)
      const intl = list.filter((c) => c !== UZBEKISTAN)
      setInternationalCountries(intl)
      if (list.includes(UZBEKISTAN)) {
        listShippingMethods(UZBEKISTAN).then(setDomesticMethods).catch(() => {})
      }
    }).catch(() => {})
  }, [])

  return (
    <div className="max-w-3xl mx-auto px-4 py-10">
      <h1 className="text-3xl font-bold mb-3">{t('delivery.title')}</h1>
      <p className="text-gray-600 mb-8">{t('delivery.subtitle')}</p>

      <section className="mb-10">
        <h2 className="text-xl font-semibold mb-3">{t('delivery.uzbekistanTitle')}</h2>
        <p className="text-sm text-gray-600 mb-3">{t('delivery.uzbekistanText')}</p>
        {domesticMethods.length > 0 && (
          <ul className="list-disc list-inside text-sm text-gray-700">
            {domesticMethods.map((m) => <li key={m}>{m}</li>)}
          </ul>
        )}
      </section>

      <section className="mb-10">
        <h2 className="text-xl font-semibold mb-3">{t('delivery.internationalTitle')}</h2>
        <p className="text-sm text-gray-600 mb-3">{t('delivery.internationalText')}</p>
        {internationalCountries.length > 0 && (
          <ul className="list-disc list-inside text-sm text-gray-700">
            {internationalCountries.map((c) => <li key={c}>{c}</li>)}
          </ul>
        )}
      </section>

      <section className="text-sm text-gray-600 space-y-2">
        <p>{t('delivery.trackingText')}</p>
        <p>{t('delivery.restrictionsText')}</p>
      </section>

      {countries.length === 0 && (
        <p className="text-sm text-gray-400 mt-6">{t('delivery.noCountries')}</p>
      )}
    </div>
  )
}
