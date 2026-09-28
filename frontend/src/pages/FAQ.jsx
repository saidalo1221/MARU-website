import { useEffect, useState } from 'react'
import { useLocale } from '../context/LocaleContext'
import { listPageSections } from '../api/pageSections'

function FaqItem({ question, answer }) {
  const [open, setOpen] = useState(false)
  return (
    <div className="border-b border-gray-200 py-3">
      <button
        onClick={() => setOpen((o) => !o)}
        className="flex w-full justify-between items-center text-left text-sm font-medium"
        aria-expanded={open}
      >
        {question}
        <span className="text-gray-400">{open ? '−' : '+'}</span>
      </button>
      {open && <p className="text-sm text-gray-600 mt-2">{answer}</p>}
    </div>
  )
}

export default function FAQ() {
  const { t, locale } = useLocale()
  const [sections, setSections] = useState([])

  useEffect(() => {
    listPageSections('faq', locale).then(setSections).catch(() => {})
  }, [locale])

  return (
    <div className="max-w-3xl mx-auto px-4 py-10">
      <h1 className="text-3xl font-bold mb-8">{t('faq.title')}</h1>
      <div>
        {sections.map((s) => (
          <FaqItem key={s.id} question={s.title} answer={s.body} />
        ))}
      </div>
      {sections.length === 0 && <p className="text-gray-400 text-sm">{t('faq.empty')}</p>}
    </div>
  )
}
