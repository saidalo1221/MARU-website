import { useEffect, useState } from 'react'
import { useLocale } from '../context/LocaleContext'
import { getSiteSettings } from '../api/siteSettings'
import { listAboutSections } from '../api/aboutSections'
import InfoSections from '../components/layout/InfoSections'
import PageIntro from '../components/layout/PageIntro'
import Seo from '../components/Seo'

export default function About() {
  const { locale, t } = useLocale()
  const [settings, setSettings] = useState(null)
  const [sections, setSections] = useState([])

  useEffect(() => {
    getSiteSettings(locale).then(setSettings).catch(() => {})
    listAboutSections(locale).then(setSections).catch(() => {})
  }, [locale])

  return (
    <div className="max-w-4xl mx-auto px-4 py-12 md:py-16">
      <Seo title={settings?.about_title || t('about.title')} description={settings?.about_body} />
      <PageIntro title={settings?.about_title || t('about.title')} subtitle={settings?.about_body || t('about.subtitle')} />
      <InfoSections sections={sections} />
    </div>
  )
}
