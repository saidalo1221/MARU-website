import { useLocale } from '../context/LocaleContext'
import InquiryForm from '../components/forms/InquiryForm'

export default function Distributor() {
  const { t } = useLocale()
  const sections = [
    ['distributor.aboutTitle', 'distributor.aboutText'],
    ['distributor.capabilitiesTitle', 'distributor.capabilitiesText'],
    ['distributor.rangeTitle', 'distributor.rangeText'],
    ['distributor.marketsTitle', 'distributor.marketsText'],
    ['distributor.termsTitle', 'distributor.termsText'],
    ['distributor.logisticsTitle', 'distributor.logisticsText'],
  ]

  return (
    <div className="max-w-5xl mx-auto px-4 py-10">
      <h1 className="text-3xl font-bold mb-3">{t('distributor.title')}</h1>
      <p className="text-gray-600 mb-8">{t('distributor.subtitle')}</p>

      <div className="grid sm:grid-cols-2 gap-6 mb-10">
        {sections.map(([titleKey, textKey]) => (
          <div key={titleKey}>
            <h2 className="font-semibold mb-1">{t(titleKey)}</h2>
            <p className="text-sm text-gray-600">{t(textKey)}</p>
          </div>
        ))}
      </div>

      <div className="max-w-lg border border-gray-200 rounded-lg p-6">
        <h2 className="text-lg font-semibold mb-4">{t('distributor.formTitle')}</h2>
        <InquiryForm defaultType="distributor" lockType ctaKey="distributor.cta" />
      </div>
    </div>
  )
}
