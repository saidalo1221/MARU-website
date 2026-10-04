import { useLocale } from '../context/LocaleContext'
import InquiryForm from '../components/forms/InquiryForm'
import InfoSections from '../components/layout/InfoSections'
import PageIntro from '../components/layout/PageIntro'
import Seo from '../components/Seo'

export default function Distributor() {
  const { t } = useLocale()
  const sections = [
    ['distributor.aboutTitle', 'distributor.aboutText'],
    ['distributor.capabilitiesTitle', 'distributor.capabilitiesText'],
    ['distributor.rangeTitle', 'distributor.rangeText'],
    ['distributor.marketsTitle', 'distributor.marketsText'],
    ['distributor.termsTitle', 'distributor.termsText'],
    ['distributor.logisticsTitle', 'distributor.logisticsText'],
  ].map(([titleKey, textKey]) => ({ id: titleKey, title: t(titleKey), body: t(textKey) }))

  return (
    <div className="max-w-4xl mx-auto px-4 py-12 md:py-16">
      <Seo title={t('distributor.title')} description={t('distributor.subtitle')} />
      <PageIntro title={t('distributor.title')} subtitle={t('distributor.subtitle')} />

      <InfoSections sections={sections} className="mb-12" />

      <div className="mx-auto max-w-xl rounded-3xl border border-gray-200 bg-gray-50 p-6 md:p-8">
        <h2 className="mb-5 text-xl font-semibold">{t('distributor.formTitle')}</h2>
        <InquiryForm defaultType="distributor" lockType ctaKey="distributor.cta" />
      </div>
    </div>
  )
}
