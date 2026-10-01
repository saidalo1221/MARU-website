import { useEffect, useState } from 'react'
import { useLocale } from '../context/LocaleContext'
import { listPageSections } from '../api/pageSections'
import Seo from '../components/Seo'
import FaqItem from '../components/FaqItem'

const FAQ_CATEGORIES = ['general', 'products', 'orders', 'payment', 'delivery', 'returns', 'wholesale', 'international']

export default function FAQ() {
  const { t, locale } = useLocale()
  const [sections, setSections] = useState([])

  // Questions grouped by topic, in a fixed order; untagged ones come first as "general".
  const groups = FAQ_CATEGORIES
    .map((key) => ({ key, items: sections.filter((s) => (s.category || 'general') === key) }))
    .filter((g) => g.items.length > 0)

  useEffect(() => {
    listPageSections('faq', locale).then(setSections).catch(() => {})
  }, [locale])

  return (
    <div className="max-w-3xl mx-auto px-4 py-10">
      <Seo title={t('faq.title')} />
      <h1 className="text-3xl font-bold mb-8">{t('faq.title')}</h1>
      {groups.map((group) => (
        <section key={group.key} className="mb-8" aria-labelledby={`faq-${group.key}`}>
          {groups.length > 1 && <h2 id={`faq-${group.key}`} className="text-lg font-semibold mb-1">{t(`faq.category.${group.key}`)}</h2>}
          {group.items.map((s) => (
            <FaqItem key={s.id} question={s.title} answer={s.body} />
          ))}
        </section>
      ))}
      {sections.length === 0 && <p className="text-gray-500 text-sm">{t('faq.empty')}</p>}
    </div>
  )
}
