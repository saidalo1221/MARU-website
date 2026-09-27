import { LOCALES, useLocale } from '../context/LocaleContext'

const LABELS = { ru: 'RU', uz: 'UZ', en: 'EN' }

export default function LanguageSwitcher() {
  const { locale, setLocale, t } = useLocale()

  return (
    <select
      value={locale}
      onChange={(e) => setLocale(e.target.value)}
      className="bg-transparent text-sm border border-gray-300 rounded px-2 py-1"
      aria-label={t('language.ariaLabel')}
    >
      {LOCALES.map((code) => (
        <option key={code} value={code}>
          {LABELS[code]}
        </option>
      ))}
    </select>
  )
}
