import { useEffect, useState } from 'react'
import { useLocale } from '../context/LocaleContext'
import { listShippingCountries, listShippingMethods } from '../api/shipping'
import { listPageSections } from '../api/pageSections'
import Seo from '../components/Seo'

const UZBEKISTAN = 'Uzbekistan'

export default function Delivery() {
  const { t, locale } = useLocale()
  const [countries, setCountries] = useState([])
  const [domesticMethods, setDomesticMethods] = useState([])
  const [internationalCountries, setInternationalCountries] = useState([])
  const [sections, setSections] = useState([])

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

  useEffect(() => {
    listPageSections('delivery', locale).then(setSections).catch(() => {})
  }, [locale])

  // Admin-managed content (app/models/page_section.py); seeded in the same
  // order as the old hardcoded copy so the two dynamic lists below still
  // land under the right section — see AdminPageSections for reordering.
  const [uzSection, intlSection, ...restSections] = sections

  return (
    <div className="max-w-3xl mx-auto px-4 py-10">
      <Seo title={t('delivery.title')} />
      <h1 className="text-3xl font-bold mb-3">{t('delivery.title')}</h1>
      <p className="text-gray-600 mb-8">{t('delivery.subtitle')}</p>

      {uzSection && (
        <section className="mb-10">
          <h2 className="text-xl font-semibold mb-3">{uzSection.title}</h2>
          <p className="text-sm text-gray-600 mb-3">{uzSection.body}</p>
          {domesticMethods.length > 0 && (
            <ul className="list-disc list-inside text-sm text-gray-700">
              {domesticMethods.map((m) => <li key={m}>{m}</li>)}
            </ul>
          )}
        </section>
      )}

      {intlSection && (
        <section className="mb-10">
          <h2 className="text-xl font-semibold mb-3">{intlSection.title}</h2>
          <p className="text-sm text-gray-600 mb-3">{intlSection.body}</p>
          {internationalCountries.length > 0 && (
            <ul className="list-disc list-inside text-sm text-gray-700">
              {internationalCountries.map((c) => <li key={c}>{c}</li>)}
            </ul>
          )}
        </section>
      )}

      {restSections.length > 0 && (
        <section className="text-sm text-gray-600 space-y-2">
          {restSections.map((s) => <p key={s.id}>{s.body}</p>)}
        </section>
      )}

      {countries.length === 0 && (
        <p className="text-sm text-gray-400 mt-6">{t('delivery.noCountries')}</p>
      )}
    </div>
  )
}
