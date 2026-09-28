import { useEffect, useState } from 'react'
import { useLocale } from '../context/LocaleContext'
import { listPageSections } from '../api/pageSections'
import Seo from '../components/Seo'

export default function Returns() {
  const { t, locale } = useLocale()
  const [sections, setSections] = useState([])

  useEffect(() => {
    listPageSections('returns', locale).then(setSections).catch(() => {})
  }, [locale])

  return (
    <div className="max-w-3xl mx-auto px-4 py-10">
      <Seo title={t('returns.title')} />
      <h1 className="text-3xl font-bold mb-3">{t('returns.title')}</h1>
      <p className="text-gray-600 mb-8">{t('returns.subtitle')}</p>

      <div className="space-y-6 mb-8">
        {sections.map((s) => (
          <div key={s.id}>
            <h2 className="font-semibold mb-1">{s.title}</h2>
            <p className="text-sm text-gray-600">{s.body}</p>
          </div>
        ))}
      </div>

      <p className="text-sm text-gray-500">{t('returns.contactText')}</p>
    </div>
  )
}
