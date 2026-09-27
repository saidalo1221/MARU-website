import { useLocale } from '../context/LocaleContext'

export default function About() {
  const { t } = useLocale()
  const sections = [
    ['about.historyTitle', 'about.historyText'],
    ['about.companyTitle', 'about.companyText'],
    ['about.productionTitle', 'about.productionText'],
    ['about.equipmentTitle', 'about.equipmentText'],
    ['about.qualityTitle', 'about.qualityText'],
    ['about.productsTitle', 'about.productsText'],
    ['about.marketsTitle', 'about.marketsText'],
  ]

  return (
    <div className="max-w-3xl mx-auto px-4 py-10">
      <h1 className="text-3xl font-bold mb-3">{t('about.title')}</h1>
      <p className="text-gray-600 mb-10">{t('about.subtitle')}</p>

      <div className="space-y-8">
        {sections.map(([titleKey, textKey]) => (
          <div key={titleKey}>
            <h2 className="text-lg font-semibold mb-1">{t(titleKey)}</h2>
            <p className="text-sm text-gray-600">{t(textKey)}</p>
          </div>
        ))}
      </div>
    </div>
  )
}
