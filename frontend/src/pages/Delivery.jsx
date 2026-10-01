import { useEffect, useState } from 'react'
import { useLocale } from '../context/LocaleContext'
import { getShippingEstimate, listShippingCountries, listShippingMethods } from '../api/shipping'
import { listPageSections } from '../api/pageSections'
import Seo from '../components/Seo'

const UZBEKISTAN = 'Uzbekistan'

export default function Delivery() {
  const { t, locale } = useLocale()
  const [countries, setCountries] = useState([])
  const [domesticMethods, setDomesticMethods] = useState([])
  const [internationalCountries, setInternationalCountries] = useState([])
  const [sections, setSections] = useState([])
  const [estimates, setEstimates] = useState([])

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

  // One row per country: how long delivery takes and what it costs from.
  useEffect(() => {
    if (countries.length === 0) return
    Promise.all(countries.map((c) => getShippingEstimate(c).then((e) => ({ country: c, ...e })).catch(() => ({ country: c }))))
      .then(setEstimates)
  }, [countries])

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

      {estimates.length > 0 && (
        <section className="mb-10 overflow-x-auto">
          <h2 className="text-xl font-semibold mb-3">{t('delivery.tableTitle')}</h2>
          <table className="w-full text-sm border border-gray-200">
            <thead className="bg-gray-50 text-left">
              <tr>
                <th scope="col" className="px-3 py-2">{t('admin.common.country')}</th>
                <th scope="col" className="px-3 py-2">{t('delivery.tableTime')}</th>
                <th scope="col" className="px-3 py-2">{t('delivery.tableCost')}</th>
                <th scope="col" className="px-3 py-2">{t('delivery.tableFree')}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {estimates.map((e) => (
                <tr key={e.country}>
                  <th scope="row" className="px-3 py-2 text-left font-medium">{e.country}</th>
                  <td className="px-3 py-2">
                    {e.max_days != null
                      ? t('orderStatus.estimatedDays', { days: e.min_days != null && e.min_days !== e.max_days ? `${e.min_days}–${e.max_days}` : e.max_days })
                      : '—'}
                  </td>
                  <td className="px-3 py-2">
                    {e.from_fee == null ? '—' : Number(e.from_fee) === 0 ? t('productDetail.deliveryFree') : `${e.fee_currency} ${Number(e.from_fee).toFixed(2)}`}
                  </td>
                  <td className="px-3 py-2">
                    {e.free_shipping_threshold != null ? `${e.currency} ${Number(e.free_shipping_threshold).toFixed(0)}` : '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}

      {countries.length === 0 && (
        <p className="text-sm text-gray-500 mt-6">{t('delivery.noCountries')}</p>
      )}
    </div>
  )
}
