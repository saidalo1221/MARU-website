import { useEffect, useState } from 'react'
import { useLocale } from '../context/LocaleContext'
import { listPageSections } from '../api/pageSections'
import InfoSections from '../components/layout/InfoSections'
import PageIntro from '../components/layout/PageIntro'
import Seo from '../components/Seo'

export default function Returns() {
  const { t, locale } = useLocale()
  const [sections, setSections] = useState([])

  useEffect(() => {
    listPageSections('returns', locale).then(setSections).catch(() => {})
  }, [locale])

  return (
    <div className="max-w-4xl mx-auto px-4 py-12 md:py-16">
      <Seo title={t('returns.title')} />
      <PageIntro title={t('returns.title')} subtitle={t('returns.subtitle')} />

      <InfoSections sections={sections} className="mb-8" />

      <p className="rounded-3xl bg-brand-light px-6 py-8 text-center text-gray-700">{t('returns.contactText')}</p>
    </div>
  )
}
