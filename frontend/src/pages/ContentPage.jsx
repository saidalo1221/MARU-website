import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { listPageSections } from '../api/pageSections'
import { useLocale } from '../context/LocaleContext'
import Seo from '../components/Seo'

// A page whose body is made of admin-editable sections (Admin > Support Pages
// Content), e.g. Manufacturing and Quality (PRD ТЗ№2 §34). Nothing is shown
// that an admin hasn't entered, so no unverified claims appear by default.
export default function ContentPage({ pageKey }) {
  const { t, locale } = useLocale()
  const [sections, setSections] = useState([])
  const [loaded, setLoaded] = useState(false)

  useEffect(() => {
    listPageSections(pageKey, locale)
      .then(setSections)
      .catch(() => {})
      .finally(() => setLoaded(true))
  }, [pageKey, locale])

  const title = t(`contentPages.${pageKey}Title`)
  return (
    <div className="max-w-3xl mx-auto px-4 py-10">
      <Seo title={title} />
      <h1 className="text-3xl font-bold mb-3">{title}</h1>
      <p className="text-gray-600 mb-8">{t(`contentPages.${pageKey}Subtitle`)}</p>

      <div className="space-y-6 mb-8">
        {sections.map((s) => (
          <div key={s.id}>
            <h2 className="font-semibold mb-1">{s.title}</h2>
            <p className="text-sm text-gray-600 whitespace-pre-wrap">{s.body}</p>
          </div>
        ))}
      </div>
      {loaded && sections.length === 0 && <p className="text-sm text-gray-500 mb-6">{t('contentPages.empty')}</p>}

      <div className="flex flex-wrap gap-4 text-sm">
        <Link to="/about" className="text-brand underline">{t('header.company')}</Link>
        <Link to="/contact" className="text-brand underline">{t('footer.contact')}</Link>
      </div>
    </div>
  )
}
