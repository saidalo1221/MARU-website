import { useState } from 'react'
import { useLocale } from '../context/LocaleContext'

const CATEGORIES = ['products', 'orders', 'payment', 'delivery', 'returns', 'wholesale', 'international']
const QUESTIONS_PER_CATEGORY = 3

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
  const { t } = useLocale()

  return (
    <div className="max-w-3xl mx-auto px-4 py-10">
      <h1 className="text-3xl font-bold mb-8">{t('faq.title')}</h1>

      <div className="space-y-10">
        {CATEGORIES.map((cat) => (
          <div key={cat}>
            <h2 className="text-lg font-semibold mb-2">{t(`faq.category.${cat}`)}</h2>
            <div>
              {Array.from({ length: QUESTIONS_PER_CATEGORY }, (_, i) => i + 1).map((n) => (
                <FaqItem
                  key={n}
                  question={t(`faq.${cat}.q${n}`)}
                  answer={t(`faq.${cat}.a${n}`)}
                />
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
