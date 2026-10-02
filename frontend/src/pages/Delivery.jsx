import { useEffect, useState } from 'react'
import { useLocale } from '../context/LocaleContext'
import { getShippingEstimate, listShippingCountries, listShippingMethods } from '../api/shipping'
import { listPageSections } from '../api/pageSections'
import PageIntro from '../components/layout/PageIntro'
import Seo from '../components/Seo'

const UZBEKISTAN = 'Uzbekistan'

// A soft panel for one delivery zone: text, then the methods or countries as pills.
function ZonePanel({ section, items, tone }) {
  return (
    <section className={`rounded-3xl p-6 md:p-8 ${tone}`}>
      <h2 className="mb-2 text-xl font-semibold">{section.title}</h2>
      <p className="mb-4 text-gray-600">{section.body}</p>
      {items.length > 0 && (
        <ul className="flex flex-wrap gap-2">
          {items.map((item) => (
            <li key={item} className="rounded-full border border-gray-300 bg-white/70 px-3 py-1 text-sm">{item}</li>
          ))}
        </ul>
      )}
    </section>
  )
}

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
  // land under the right section. See AdminPageSections for reordering.
  const [uzSection, intlSection, ...restSections] = sections

  return (
    <div className="max-w-4xl mx-auto px-4 py-12 md:py-16">
      <Seo title={t('delivery.title')} />
      <PageIntro title={t('delivery.title')} subtitle={t('delivery.subtitle')} />

      {(uzSection || intlSection) && (
        <div className="mb-10 grid gap-4 md:grid-cols-2">
          {uzSection && <ZonePanel section={uzSection} items={domesticMethods} tone="bg-brand-light" />}
          {intlSection && <ZonePanel section={intlSection} items={internationalCountries} tone="border border-gray-200 bg-gray-50" />}
        </div>
      )}

      {restSections.length > 0 && (
        <section className="mb-10 space-y-2 text-gray-600">
          {restSections.map((s) => <p key={s.id}>{s.body}</p>)}
        </section>
      )}

      {estimates.length > 0 && (
        <section className="mb-10">
          <h2 className="mb-4 text-2xl font-semibold tracking-tight">{t('delivery.tableTitle')}</h2>
          <div className="overflow-x-auto rounded-3xl border border-gray-200">
            <table className="w-full text-sm">
              <thead className="bg-brand-light text-left">
                <tr>
                  <th scope="col" className="px-4 py-3">{t('admin.common.country')}</th>
                  <th scope="col" className="px-4 py-3">{t('delivery.tableTime')}</th>
                  <th scope="col" className="px-4 py-3">{t('delivery.tableCost')}</th>
                  <th scope="col" className="px-4 py-3">{t('delivery.tableFree')}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {estimates.map((e) => (
                  <tr key={e.country}>
                    <th scope="row" className="px-4 py-3 text-left font-medium">{e.country}</th>
                    <td className="px-4 py-3">
                      {e.max_days != null
                        ? t('orderStatus.estimatedDays', { days: e.min_days != null && e.min_days !== e.max_days ? `${e.min_days}-${e.max_days}` : e.max_days })
                        : '-'}
                    </td>
                    <td className="px-4 py-3">
                      {e.from_fee == null ? '-' : Number(e.from_fee) === 0 ? t('productDetail.deliveryFree') : `${e.fee_currency} ${Number(e.from_fee).toFixed(2)}`}
                    </td>
                    <td className="px-4 py-3">
                      {e.free_shipping_threshold != null ? `${e.currency} ${Number(e.free_shipping_threshold).toFixed(0)}` : '-'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}

      {countries.length === 0 && (
        <p className="mt-6 rounded-3xl bg-brand-light px-6 py-10 text-center text-gray-700">{t('delivery.noCountries')}</p>
      )}
    </div>
  )
}
