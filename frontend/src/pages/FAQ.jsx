import { useEffect, useState } from 'react'
import { useLocale } from '../context/LocaleContext'
import { listPageSections } from '../api/pageSections'
import Seo from '../components/Seo'
import FaqItem from '../components/FaqItem'

export default function FAQ() {
  const { t, locale } = useLocale()
  const [sections, setSections] = useState([])

  useEffect(() => {
    listPageSections('faq', locale).then(setSections).catch(() => {})
  }, [locale])

  return (
    <div className="max-w-3xl mx-auto px-4 py-10">
      <Seo title={t('faq.title')} />
      <h1 className="text-3xl font-bold mb-8">{t('faq.title')}</h1>
      <div>
        {sections.map((s) => (
          <FaqItem key={s.id} question={s.title} answer={s.body} />
        ))}
      </div>
      {sections.length === 0 && <p className="text-gray-500 text-sm">{t('faq.empty')}</p>}
    </div>
  )
}
