import { useEffect, useState } from 'react'
import { useLocale } from '../context/LocaleContext'
import { getPaymentMethods } from '../api/orders'
import { listPageSections } from '../api/pageSections'
import InfoSections from '../components/layout/InfoSections'
import PageIntro from '../components/layout/PageIntro'
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
    <div className="max-w-4xl mx-auto px-4 py-12 md:py-16">
      <Seo title={t('payment.title')} />
      <PageIntro title={t('payment.title')} subtitle={t('payment.subtitle')} />
      <p className="-mt-6 mb-8 text-center text-sm text-gray-500 md:-mt-8">{country ? t('payment.forCountry', { country }) : t('payment.chooseCountry')}</p>

      {enabled.length > 0 ? (
        <ul className="mb-10 grid gap-3 sm:grid-cols-2">
          {enabled.map((m) => (
            <li key={m.id} className="flex items-center justify-between gap-3 rounded-2xl border border-gray-200 bg-gray-50 px-6 py-4">
              <span className="font-semibold">{m.display_name}</span>
              <span className="rounded-full bg-brand-light px-3 py-1 text-xs font-medium text-green-700">{t('payment.available')}</span>
            </li>
          ))}
        </ul>
      ) : (
        <p className="mb-10 rounded-3xl bg-brand-light px-6 py-10 text-center text-gray-700">{t('payment.noneAvailable')}</p>
      )}

      <InfoSections sections={sections} />
    </div>
  )
}
