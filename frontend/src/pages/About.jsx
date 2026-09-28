import { useEffect, useState } from 'react'
import { useLocale } from '../context/LocaleContext'
import { getSiteSettings } from '../api/siteSettings'
import { listAboutSections } from '../api/aboutSections'

export default function About() {
  const { locale, t } = useLocale()
  const [settings, setSettings] = useState(null)
  const [sections, setSections] = useState([])

  useEffect(() => {
    getSiteSettings(locale).then(setSettings).catch(() => {})
    listAboutSections(locale).then(setSections).catch(() => {})
  }, [locale])

  return (
    <div className="max-w-3xl mx-auto px-4 py-10">
      <h1 className="text-3xl font-bold mb-3">{settings?.about_title || t('about.title')}</h1>
      <p className="text-gray-600 mb-10">{settings?.about_body || t('about.subtitle')}</p>

      <div className="space-y-8">
        {sections.map((s) => (
          <div key={s.id}>
            <h2 className="text-lg font-semibold mb-1">{s.title}</h2>
            <p className="text-sm text-gray-600 whitespace-pre-wrap">{s.body}</p>
          </div>
        ))}
      </div>
    </div>
  )
}
