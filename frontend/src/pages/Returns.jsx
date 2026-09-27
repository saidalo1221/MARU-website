import { useLocale } from '../context/LocaleContext'

export default function Returns() {
  const { t } = useLocale()
  const sections = [
    ['returns.conditionsTitle', 'returns.conditionsText'],
    ['returns.timeframeTitle', 'returns.timeframeText'],
    ['returns.procedureTitle', 'returns.procedureText'],
    ['returns.exceptionsTitle', 'returns.exceptionsText'],
  ]

  return (
    <div className="max-w-3xl mx-auto px-4 py-10">
      <h1 className="text-3xl font-bold mb-3">{t('returns.title')}</h1>
      <p className="text-gray-600 mb-8">{t('returns.subtitle')}</p>

      <div className="space-y-6 mb-8">
        {sections.map(([titleKey, textKey]) => (
          <div key={titleKey}>
            <h2 className="font-semibold mb-1">{t(titleKey)}</h2>
            <p className="text-sm text-gray-600">{t(textKey)}</p>
          </div>
        ))}
      </div>

      <p className="text-sm text-gray-500">{t('returns.contactText')}</p>
    </div>
  )
}
